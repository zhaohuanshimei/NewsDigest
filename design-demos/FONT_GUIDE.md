# News Digest 字体选择指南

## 报纸风格字体推荐

### 英文字体（衬线体）

| 字体名称 | 特点 | 适用场景 | Google Fonts |
|----------|------|----------|--------------|
| **Playfair Display** | 高对比度、优雅、现代感 | 标题、品牌名 | ✅ |
| **Libre Baskerville** | 经典、易读、传统 | 正文、长文本 | ✅ |
| **EB Garamond** | 古典、优雅、人文主义 | 标题、正文 | ✅ |
| **Merriweather** | 专为屏幕设计、高可读性 | 正文、长文本 | ✅ |
| **Lora** | 现代衬线、平衡、温暖 | 正文、标题 | ✅ |
| **Source Serif Pro** | Adobe 出品、专业、清晰 | 正文、标题 | ✅ |
| **Cormorant Garamond** | 优雅、高对比度、时尚 | 标题、品牌名 | ✅ |
| **DM Serif Display** | 现代、大胆、有力 | 标题、大标题 | ✅ |

### 中文字体（宋体类）

| 字体名称 | 特点 | 适用场景 | 备注 |
|----------|------|----------|------|
| **思源宋体 (Source Han Serif)** | 优雅、专业、多字重 | 标题、正文 | Google Fonts / Adobe |
| **Noto Serif SC** | 与思源宋体同源、Web 优化 | 标题、正文 | Google Fonts |
| **方正书宋** | 传统、正式、印刷感 | 正文 | 商用需授权 |
| **华文宋体** | macOS/iOS 内置、优雅 | 正文 | 系统字体 |
| **宋体 (SimSen)** | Windows 内置、传统 | 正文 | 系统字体 |

### 中英文字体搭配推荐

#### 方案 1：经典报纸风格（推荐）
```
英文标题：Playfair Display (700)
英文正文：Libre Baskerville (400)
中文标题：思源宋体 / Noto Serif SC (700)
中文正文：思源宋体 / Noto Serif SC (400)
```
**效果**：经典、权威、专业

#### 方案 2：现代优雅风格
```
英文标题：Cormorant Garamond (600)
英文正文：Source Serif Pro (400)
中文标题：思源宋体 (600)
中文正文：思源宋体 (400)
```
**效果**：优雅、现代、精致

#### 方案 3：传统印刷风格
```
英文标题：EB Garamond (700)
英文正文：EB Garamond (400)
中文标题：方正书宋 (700)
中文正文：方正书宋 (400)
```
**效果**：传统、印刷感、人文气息

#### 方案 4：现代报纸风格
```
英文标题：DM Serif Display (400)
英文正文：Merriweather (400)
中文标题：Noto Serif SC (700)
中文正文：Noto Serif SC (400)
```
**效果**：现代、清晰、易读

## 字体搭配原则

1. **对比原则**：英文衬线 + 中文宋体，保持风格一致
2. **层次原则**：标题用高字重，正文用常规字重
3. **可读性原则**：正文优先考虑屏幕可读性
4. **加载速度**：优先使用 Google Fonts 或系统字体

## 字体加载策略

```css
/* 方案 1：Google Fonts 加载 */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Libre+Baskerville:wght@400;700&family=Noto+Serif+SC:wght@400;700&display=swap');

/* 方案 2：系统字体回退 */
:root {
  --font-en-title: 'Playfair Display', 'Georgia', serif;
  --font-en-body: 'Libre Baskerville', 'Georgia', serif;
  --font-zh: 'Noto Serif SC', 'Source Han Serif SC', '华文宋体', '宋体', serif;
}
```

## 你的选择

基于你喜欢的报纸风格，推荐使用 **方案 1：经典报纸风格**：
- 英文标题：Playfair Display（优雅、现代、有特色）
- 英文正文：Libre Baskerville（经典、易读）
- 中文标题/正文：思源宋体 / Noto Serif SC（专业、优雅）
