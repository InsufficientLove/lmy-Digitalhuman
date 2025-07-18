# 占位符图片说明

请在此位置放置一个名为 `placeholder.jpg` 的占位符图片。

## 图片要求

- 文件名：`placeholder.jpg`
- 尺寸：512x512 像素
- 格式：JPG
- 内容：提示用户上传头像的图标或文字

## 建议内容

- 一个简单的人像轮廓图标
- 或者带有 "点击上传头像" 文字的图片
- 背景色建议使用浅灰色 (#f0f0f0)

## 示例代码

如果您需要程序生成占位符图片，可以使用以下代码：

```html
<!-- 简单的SVG占位符 -->
<svg width="512" height="512" xmlns="http://www.w3.org/2000/svg">
  <rect width="512" height="512" fill="#f0f0f0"/>
  <circle cx="256" cy="200" r="60" fill="#ccc"/>
  <path d="M150 350 Q256 280 362 350" fill="#ccc"/>
  <text x="256" y="450" text-anchor="middle" font-family="Arial" font-size="24" fill="#666">点击上传头像</text>
</svg>
``` 