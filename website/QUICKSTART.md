# GitCloud Website - Quick Start Guide

## 🚀 最快启动方式

### 方法 1: 使用启动脚本（推荐）

```bash
cd website
./start-server.sh
```

然后在浏览器中打开：**http://localhost:8000**

### 方法 2: 直接打开 HTML

在 `website` 目录中双击 `index.html` 文件，或者：

```bash
cd website
open index.html  # macOS
```

## 📋 网站功能

### 核心动画

网站的核心是一个交互式动画，展示了 GitCloud 的工作流程：

1. **GitHub Repository** - 输入 GitHub 项目 URL
2. **AI Analysis** - AI 分析项目结构和依赖
3. **Cloud Provisioning** - 自动创建云资源（CVM、MySQL）
4. **Your App is Live** - 项目成功运行

### 交互方式

- **自动播放**：滚动到工作流程区域时自动开始动画
- **时间轴控制**：点击底部的时间轴圆点跳转到特定阶段
- **重播按钮**：点击"Replay Animation"按钮重新播放
- **键盘快捷键**：按 `R` 键快速重播动画

## 🎨 设计特点

- **深色主题**：现代科技感的深色界面
- **渐变色彩**：紫蓝色渐变突出重点
- **平滑动画**：CSS 和 JavaScript 结合实现流畅的过渡效果
- **响应式设计**：支持桌面、平板和手机
- **粒子背景**：微妙的动态粒子效果增强氛围

## 📱 浏览器兼容性

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ 移动端浏览器

## 🛠️ 自定义

### 修改颜色主题

编辑 `css/style.css` 中的 CSS 变量：

```css
:root {
    --color-accent: #6366f1;  /* 主要强调色 */
    --color-bg: #0a0a0f;      /* 背景色 */
    /* ... */
}
```

### 调整动画速度

编辑 `js/main.js`：

```javascript
this.animationSpeed = 1500; // 毫秒，每个阶段的持续时间
```

### 修改内容

- 编辑 `index.html` 修改文字内容
- 修改工作流程阶段的示例数据
- 更新安装命令和链接

## 📦 部署到生产环境

### GitHub Pages

```bash
# 在项目根目录
git add website/
git commit -m "Add GitCloud website"
git push

# 在 GitHub 仓库设置中启用 GitHub Pages
# 选择 main 分支的 /website 文件夹
```

### Netlify

1. 拖拽 `website` 文件夹到 [Netlify Drop](https://app.netlify.com/drop)
2. 完成！获得一个 `https://xxx.netlify.app` 域名

### Vercel

```bash
cd website
npx vercel deploy
```

## 🎯 性能优化

### 如果粒子背景导致卡顿

编辑 `js/main.js`，注释掉这一行：

```javascript
// createParticleBackground();
```

### 减少粒子数量

```javascript
const particleCount = 30; // 从 50 减少到 30
```

## 📝 文件说明

- `index.html` - 主 HTML 文件，包含所有页面结构
- `css/style.css` - 完整的样式表，包含所有动画
- `js/main.js` - JavaScript 交互逻辑和动画控制器
- `start-server.sh` - 便捷的本地服务器启动脚本
- `README.md` - 详细的技术文档
- `QUICKSTART.md` - 本快速入门指南

## 💡 提示

1. **最佳体验**：使用 Chrome 或 Firefox 浏览器
2. **动画流畅度**：确保浏览器硬件加速已启用
3. **移动端**：横屏查看效果更佳
4. **开发模式**：使用浏览器开发者工具查看动画细节

## 🐛 常见问题

### 动画不播放

- 确保 JavaScript 已启用
- 检查浏览器控制台是否有错误
- 尝试刷新页面

### 样式显示异常

- 确认 CSS 文件路径正确
- 清除浏览器缓存
- 检查是否使用了不支持的旧版浏览器

### 本地服务器无法启动

- 检查 8000 端口是否被占用
- 确认已安装 Python 3
- 尝试使用其他端口：`python3 -m http.server 8080`

## 📧 反馈

如有问题或建议，欢迎：
- 在 GitHub 项目中提 Issue
- 通过项目主页联系方式反馈

---

**享受 GitCloud 网站！** 🚀
