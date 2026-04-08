# 测字算事 - 调试指南

## 问题诊断

从我的环境测试Vercel时发现SSL/连接问题，这说明**Vercel项目可能有访问保护设置**。

## 请检查以下设置

### 1. Vercel Dashboard 检查
登录 https://vercel.com → 进入 zi-cesuan 项目 → Settings → Protection

**确保以下开关都是 OFF：**
- ✅ Vercel Authentication - **关闭**
- ✅ Password Protection - **关闭**
- ✅ SSO Protection - **关闭**

### 2. 本地测试（推荐）

在你的电脑上运行：

```bash
cd ~/.openclaw/workspace/zi-cesuan
source .venv/bin/activate
python test_api.py
```

这会在本地5003端口启动服务器并测试所有API。

### 3. 浏览器直接测试

在手机浏览器中打开：
```
https://zi-cesuan.vercel.app/api/cezi
```

应该返回JSON数据，如果显示"登录"或"认证"页面，说明需要关闭保护。

### 4. 微信开发者工具测试

1. 打开微信开发者工具
2. 添加项目：https://zi-cesuan.vercel.app
3. 尝试测字操作
4. 查看Console和Network中的错误

### 5. 抓包分析

在手机上：
1. 设置 → HTTP代理 → 手动设置代理到电脑IP的8888端口
2. 在电脑上运行 `charles` 或开启抓包
3. 查看测字请求的详细错误

---

**最快解决方案：关闭Vercel的所有访问保护**
