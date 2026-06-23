# News Digest Logo 设计规则

## 1. Logo 设计原则

### 核心原则
- **简洁性**：Logo 必须在 24x24px 小尺寸下清晰可辨
- **一致性**：所有 Logo 使用统一的容器、字体、颜色系统
- **可扩展性**：新源添加时，按规则自动生成 Logo

### 设计规则

#### 命名规则
| 源名称 | Logo 文本 | 规则 |
|--------|----------|------|
| The Guardian | Guardian | 去掉 "The"，保留核心词 |
| New York Times | NYT | 使用首字母缩写 |
| Associated Press | AP | 使用首字母缩写 |
| BBC World | BBC | 使用品牌缩写 |
| Bloomberg | Bloomberg | 名称 ≤ 9 字符，全称 |
| Financial Times | FT | 使用首字母缩写 |
| The Economist | Economist | 去掉 "The"，保留核心词 |
| Al Jazeera | Al Jazeera | 名称 ≤ 9 字符，全称 |
| Washington Post | WaPo | 使用常见缩写 |
| Reuters | Reuters | 名称 ≤ 9 字符，全称 |

#### 规则总结
1. **名称 ≤ 9 字符**：使用全称
2. **名称 > 9 字符**：使用首字母缩写或去掉 "The" 等前缀
3. **有通用缩写**：使用通用缩写（如 NYT, BBC, AP, FT）
4. **无通用缩写**：使用首字母缩写

## 2. Logo 视觉规范

### 容器
```css
.source-logo {
  width: 28px;
  height: 28px;
  background: var(--logo-bg);
  border: 1px solid var(--border);
  border-radius: 2px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
```

### 字体
```css
.source-logo {
  font-family: var(--font-en-title);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  line-height: 1;
}
```

### 颜色
```css
:root {
  --logo-bg: #f5f5f0;
  --logo-border: #d4d0c8;
  --logo-text: #1a1a1a;
}

/* 深色模式 */
@media (prefers-color-scheme: dark) {
  :root {
    --logo-bg: #2a2a2a;
    --logo-border: #444;
    --logo-text: #e8e8e8;
  }
}
```

## 3. Logo 布局规则

### 行内布局（推荐）
Logo 作为来源标签的一部分，行内显示，不占用额外空间。

```html
<div class="news-source">
  <span class="source-logo">NYT</span>
  <span class="source-name">New York Times</span>
</div>
```

### 样式
```css
.news-source {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 0.5rem;
}

.source-logo {
  width: 24px;
  height: 24px;
  font-size: 8px;
  /* ... 其他样式 */
}

.source-name {
  font-family: var(--font-en-title);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--accent);
}
```

## 4. Logo 生成规则（自动化）

### 输入
- 源名称（如 "The Guardian"）
- 源品牌色（可选）

### 处理逻辑
```javascript
function generateLogoText(sourceName) {
  // 1. 去掉常见前缀
  const withoutPrefix = sourceName
    .replace(/^The\s+/i, '')
    .replace(/^Associated\s+/i, 'AP')
    .replace(/^New\s+York\s+/i, 'NY');
  
  // 2. 检查是否有通用缩写
  const abbreviations = {
    'New York Times': 'NYT',
    'Associated Press': 'AP',
    'BBC World': 'BBC',
    'Financial Times': 'FT',
    'Washington Post': 'WaPo',
  };
  
  if (abbreviations[sourceName]) {
    return abbreviations[sourceName];
  }
  
  // 3. 如果名称 ≤ 9 字符，使用全称
  if (withoutPrefix.length <= 9) {
    return withoutPrefix;
  }
  
  // 4. 否则使用首字母缩写
  return withoutPrefix
    .split(/\s+/)
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 3);
}
```

## 5. 新源添加流程

1. 在 `config/sources.yaml` 添加新源
2. 系统自动生成 Logo 文本（按上述规则）
3. Logo 样式自动应用（统一容器、字体、颜色）
4. 无需手动设计

## 6. 示例

| 源名称 | Logo 文本 | Logo 样式 |
|--------|----------|----------|
| The Guardian | Guardian | `[GUARDIAN]` |
| New York Times | NYT | `[NYT]` |
| Associated Press | AP | `[AP]` |
| BBC World | BBC | `[BBC]` |
| Bloomberg | Bloomberg | `[Bloomberg]` |
| Financial Times | FT | `[FT]` |
| The Economist | Economist | `[Economist]` |
| Al Jazeera | Al Jazeera | `[Al Jazeera]` |
| Washington Post | WaPo | `[WaPo]` |
| Reuters | Reuters | `[Reuters]` |
