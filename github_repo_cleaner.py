import requests
import time
from typing import List, Optional
from dataclasses import dataclass
import click
from rich.console import Console
from rich.prompt import Confirm
from rich.progress import Progress

@dataclass
class Repository:
    name: str
    full_name: str
    private: bool

class GitHubReposCleaner:
    def __init__(self, token: str, username: str):
        self.token = token
        self.username = username
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.console = Console()
        self.base_url = 'https://api.github.com'

    def get_public_repos(self) -> List[Repository]:
        """获取用户的所有公开仓库"""
        repos = []
        page = 1
        while True:
            response = requests.get(
                f'{self.base_url}/users/{self.username}/repos',
                headers=self.headers,
                params={'page': page, 'per_page': 100, 'type': 'public'}
            )
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
                
            repos.extend([
                Repository(
                    name=repo['name'],
                    full_name=repo['full_name'],
                    private=repo['private']
                )
                for repo in page_repos
                if not repo['private']  # 只获取公开仓库
            ])
            page += 1
            
        return repos

    def get_repo_details(self, repo_name: str) -> Optional[dict]:
        """获取仓库的详细信息"""
        try:
            response = requests.get(
                f'{self.base_url}/repos/{self.username}/{repo_name}',
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.console.print(f"[red]获取仓库 {repo_name} 详情时发生错误: {str(e)}[/red]")
            return None

    def print_repo_info(self, repo_details: dict):
        """打印仓库详细信息"""
        self.console.print("\n[yellow]仓库详细信息:[/yellow]")
        self.console.print(f"[cyan]名称:[/cyan] {repo_details['full_name']}")
        self.console.print(f"[cyan]URL:[/cyan] {repo_details['html_url']}")
        self.console.print(f"[cyan]描述:[/cyan] {repo_details['description'] or '无'}")
        self.console.print(f"[cyan]创建时间:[/cyan] {repo_details['created_at']}")
        self.console.print(f"[cyan]最后更新:[/cyan] {repo_details['updated_at']}")
        self.console.print(f"[cyan]Star数:[/cyan] {repo_details['stargazers_count']}")
        self.console.print(f"[cyan]Fork数:[/cyan] {repo_details['forks_count']}")
        self.console.print(f"[cyan]语言:[/cyan] {repo_details['language'] or '未指定'}")
        self.console.print(f"[cyan]是否为fork:[/cyan] {'是' if repo_details['fork'] else '否'}")
        if repo_details.get('license'):
            self.console.print(f"[cyan]许可证:[/cyan] {repo_details['license']['name']}")

    def verify_token(self) -> bool:
        """验证token权限"""
        try:
            response = requests.get(
                f'{self.base_url}/user',
                headers=self.headers
            )
            response.raise_for_status()
            user_data = response.json()
            if user_data['login'] != self.username:
                self.console.print(f"[red]警告：Token所属用户 ({user_data['login']}) 与目标用户 ({self.username}) 不匹配！[/red]")
                return False
            return True
        except requests.exceptions.RequestException as e:
            self.console.print(f"[red]Token验证失败: {str(e)}[/red]")
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 401:
                self.console.print("[yellow]提示：请确保Token有效且未过期[/yellow]")
            return False

    def verify_permissions(self) -> bool:
        """验证是否具有必要的权限"""
        try:
            response = requests.get(
                f'{self.base_url}/user',
                headers=self.headers
            )
            response.raise_for_status()
            scopes = response.headers.get('X-OAuth-Scopes', '').split(', ')
            
            required_scopes = {'delete_repo', 'repo'}
            missing_scopes = required_scopes - set(scopes)
            
            if missing_scopes:
                self.console.print(f"[red]Token缺少必要权限: {', '.join(missing_scopes)}[/red]")
                self.console.print("[yellow]请确保Token具有以下权限:[/yellow]")
                self.console.print("- delete_repo（用于删除仓库）")
                self.console.print("- repo（用于访问仓库信息）")
                return False
            return True
        except requests.exceptions.RequestException as e:
            self.console.print(f"[red]权限验证失败: {str(e)}[/red]")
            return False

    def delete_repository(self, repo_name: str) -> bool:
        """删除指定的仓库"""
        try:
            response = requests.delete(
                f'{self.base_url}/repos/{self.username}/{repo_name}',
                headers=self.headers
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            if isinstance(e, requests.exceptions.HTTPError):
                if e.response.status_code == 403:
                    error_message = "没有权限删除该仓库（403 Forbidden）"
                    self.console.print("[yellow]可能的原因：[/yellow]")
                    self.console.print("1. Token权限不足")
                    self.console.print("2. 仓库可能启用了分支保护")
                    self.console.print("3. 组织可能限制了仓库删除")
                elif e.response.status_code == 404:
                    error_message = "仓库不存在或无权访问（404 Not Found）"
            self.console.print(f"[red]删除仓库 {repo_name} 时发生错误: {error_message}[/red]")
            return False

def batch_confirm_repos(console: Console, repos: List[Repository], start_idx: int, batch_size: int) -> bool:
    """批量确认仓库删除"""
    end_idx = min(start_idx + batch_size, len(repos))
    batch_repos = repos[start_idx:end_idx]
    
    console.print("\n[bold yellow]以下仓库将被删除：[/bold yellow]")
    console.print("=" * 50)
    for idx, repo in enumerate(batch_repos, 1):
        console.print(f"[cyan]{idx}.[/cyan] {repo.full_name}")
    console.print("=" * 50)
    
    console.print("\n[bold yellow]请确认操作：[/bold yellow]")
    console.print("[white]输入 'y' 删除以上仓库[/white]")
    console.print("[white]输入 'n' 跳过以上仓库[/white]")
    return Confirm.ask("\n[bold red]是否删除这批仓库?[/bold red]")

@click.command()
@click.argument('username', required=True)
@click.option('--token', prompt='请输入GitHub Personal Access Token', 
              help='GitHub Personal Access Token，需要有delete_repo权限')
@click.option('--batch-size', default=5, help='每批确认的仓库数量')
def main(username: str, token: str, batch_size: int):
    """
    删除指定GitHub用户的所有公开仓库
    
    USERNAME: GitHub用户名
    """
    console = Console()
    
    # 创建清理器实例
    cleaner = GitHubReposCleaner(token, username)
    
    # 验证token和权限
    console.print("[yellow]正在验证Token...[/yellow]")
    if not cleaner.verify_token():
        return
    
    console.print("[yellow]正在验证权限...[/yellow]")
    if not cleaner.verify_permissions():
        return
    
    try:
        # 获取所有公开仓库
        console.print("[yellow]正在获取仓库列表...[/yellow]")
        repos = cleaner.get_public_repos()
        
        if not repos:
            console.print("[green]没有找到任何公开仓库。[/green]")
            return
            
        # 显示找到的仓库总数
        total_repos = len(repos)
        console.print(f"\n[yellow]找到 {total_repos} 个公开仓库[/yellow]")
        
        # 批量处理仓库
        current_idx = 0
        while current_idx < total_repos:
            # 获取当前批次的确认结果
            if batch_confirm_repos(console, repos, current_idx, batch_size):
                # 处理当前批次的仓库
                end_idx = min(current_idx + batch_size, total_repos)
                for idx in range(current_idx, end_idx):
                    repo = repos[idx]
                    console.print(f"\n[cyan]正在处理第 {idx + 1}/{total_repos} 个仓库[/cyan]")
                    
                    # 获取并显示仓库详细信息
                    repo_details = cleaner.get_repo_details(repo.name)
                    if repo_details:
                        cleaner.print_repo_info(repo_details)
                    
                    # 删除仓库
                    if cleaner.delete_repository(repo.name):
                        console.print(f"[green]✓ 成功删除仓库: {repo.full_name}[/green]")
                    else:
                        console.print(f"[red]✗ 删除仓库失败: {repo.full_name}[/red]")
                    
                    # 显示进度
                    progress_percentage = ((idx + 1) / total_repos) * 100
                    console.print(f"\n[blue]总进度: {progress_percentage:.1f}% ({idx + 1}/{total_repos})[/blue]")
                    console.print("=" * 50)
                    
                    # 添加延迟以避免触发API限制
                    time.sleep(1)
            else:
                # 跳过当前批次的仓库
                end_idx = min(current_idx + batch_size, total_repos)
                for idx in range(current_idx, end_idx):
                    repo = repos[idx]
                    console.print(f"[yellow]→ 已跳过仓库: {repo.full_name}[/yellow]")
            
            # 更新索引
            current_idx += batch_size
                
        console.print("\n[green]✨ 操作完成！[/green]")
        
    except requests.exceptions.RequestException as e:
        console.print(f"[red]发生错误: {str(e)}[/red]")
        return
    except KeyboardInterrupt:
        console.print("\n[yellow]操作已被用户中断[/yellow]")
        return

if __name__ == '__main__':
    main()