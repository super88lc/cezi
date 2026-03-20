# 腾讯云部署指南

本指南将帮助你把测字应用部署到腾讯云（Edgeone Pages + 云函数SCF）

## 架构

```
用户 → Edgeone Pages (静态前端) → API Gateway → 云函数 SCF (Python后端)
```

---

## 步骤1：创建云函数 (SCF)

### 1.1 登录腾讯云控制台
访问 https://console.cloud.tencent.com/scf

### 1.2 创建函数
1. 点击「新建函数」
2. 选择「从头创建」
3. 配置：
   - **函数名称**: `cezi-api`
   - **地域**: 选择离你最近的区域（如广州、上海、北京）
   - **运行环境**: `Python 3.10`
   - **函数类型**: `Web函数`

### 1.3 上传代码
选择「本地上传文件夹」，上传 `scf` 目录

或者使用命令行：
```bash
# 安装 Tencent Cloud CLI
npm install -g tencentcloud-sdk-nodejs

# 创建函数包
cd scf
zip -r ../cezi.zip ./

# 上传
tccli scf CreateFunction --FunctionName cezi-api --ZipFile cezi.zip --Runtime Python3.10 --Handler index.main_handler
```

### 1.4 配置触发器
1. 点击「添加触发器」
2. 选择「API网关」
3. 创建新的API网关服务
4. 记录生成的**API地址**，格式类似：
   ```
   https://service-xxx-xxx.gz.apigw.tencentcs.com/release/cezi
   ```

---

## 步骤2：部署静态前端 (Edgeone Pages)

### 2.1 登录 Edgeone Pages
访问 https://edgeone.pages.dev/

### 2.2 创建项目
1. 点击「创建站点」
2. 选择「从GitHub推送」或「直接上传」
3. 上传 `templates/index.html`

### 2.3 修改API地址
部署前，需要修改 `index.html` 中的API地址：

找到这行：
```javascript
const API_BASE = '';
```

修改为你的云函数API地址：
```javascript
const API_BASE = 'https://service-xxx-xxx.gz.apigw.tencentcs.com/release';
```

### 2.4 自定义域名（可选）
1. 在「域名管理」中添加你的域名
2. 按提示配置DNS解析

---

## 步骤3：测试

1. 打开你的前端页面
2. 输入一个汉字测试
3. 应该能正常显示测字结果

---

## 免费额度说明

| 服务 | 免费额度 |
|------|----------|
| 云函数 SCF | 100万次调用/月 |
| Edgeone Pages | 100GB/月 |
| API Gateway | 100万次调用/月 |

个人使用基本免费。

---

## 常见问题

### Q: OCR功能不能用？
A: OCR需要额外配置。目前手动输入功能正常工作。

### Q: 函数调用超时？
A: 检查 `index.py` 中的 `timeout` 设置，建议设为60秒。

### Q: 如何更新代码？
A: 
1. 修改 `scf/index.py`
2. 重新上传函数包
3. 云函数会自动更新
