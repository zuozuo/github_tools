# GitHub Repository Cleaner

一个安全可靠的命令行工具，用于批量删除GitHub账户下的公开仓库。

## 功能特性

- 支持批量删除指定用户的所有公开仓库
- 提供友好的命令行界面和进度显示
- 包含多重安全确认机制
- 详细的操作反馈和错误处理
- 支持批量确认操作
- 可自定义批量处理数量

## 安装

```bash
pip install requests click rich
```

## 获取 GitHub Personal Access Token

1. 登录到您的GitHub账户
2. 点击右上角头像，选择 `Settings`
3. 滚动到底部，点击左侧菜单中的 `Developer settings`
4. 点击左侧菜单中的 `Personal access tokens` -> `Tokens (classic)`
5. 点击 `Generate new token` -> `Generate new token (classic)`
6. 在 "Note" 字段中输入令牌用途描述（如："Repository Cleaner"）
7. 选择令牌的有效期
8. 在权限选择中，勾选：
   - `delete_repo` （必需，用于删除仓库）
   - `repo` （用于访问仓库信息）
9. 点击页面底部的 `Generate token`
10. **重要：** 立即复制生成的token并安全保存，因为它只会显示一次

## 使用方法

基本用法：
```bash
python github_repo_cleaner.py USERNAME
```

自定义批量大小：
```bash
python github_repo_cleaner.py USERNAME --batch-size 10
```

指定token（可选）：
```bash
python github_repo_cleaner.py USERNAME --token YOUR_TOKEN
```

参数说明：
- `USERNAME`: GitHub用户名（必需）
- `--token`: GitHub Personal Access Token
- `--batch-size`: 每批确认的仓库数量（默认为5）

## 安全提示

- 永远不要分享或公开您的Personal Access Token
- 建议设置合适的token有效期
- 不再使用时记得在GitHub中撤销token
- 建议先在测试账号上验证脚本行为

## 注意事项

- 删除操作是不可逆的，请在操作前备份重要数据
- 该工具仅删除公开仓库
- 操作前会显示将要删除的仓库列表并要求确认
- 遵守GitHub的API使用限制

## 作者

- Name: Zorro
- Email: zzhatzzh@gmail.com
- Github: https://github.com/zuozuo

## 许可证

MIT License