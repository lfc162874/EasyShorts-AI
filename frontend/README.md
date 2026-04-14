# EasyShorts AI Frontend

阶段二的后台前端，默认对接真实后端接口，重点覆盖新闻源管理、新闻列表、抓取记录和内容生成链路。

## 启动

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

浏览器访问：

- http://localhost:5173/

如果 5173 被占用，Vite 会自动换到下一个可用端口。

## 构建

```bash
npm run build
```

## 说明

- 开发环境下，前端会把 `/easy-shorts` 代理到本机 `http://127.0.0.1:8000`，因此登录和新闻相关接口不会被浏览器跨域拦住。
- 如果你把后端部署到别的地址，可以通过 `VITE_API_BASE_URL` 覆盖默认接口前缀。
