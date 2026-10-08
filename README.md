# PPT Studio · 160 种风格的 PPT 制作技能

把一句话需求、一份文档或一组要点，做成风格统一、可编辑的 PPT。
**AI Agent 阅读完整风格提示词，根据内容设计每页构图，直接完成排版，再渲染检查。**
生图用于所需的照片、插画、抠图和纹理；标题、信息结构、图表和几何装饰由 Agent 排版。

## 工作流程

1. **需求与大纲**：明确受众、目的和事实来源，写每页内容与备注。
2. **阅读风格**：从 160 套文字规格中选择，读取完整原文及中文翻译。
3. **Agent 构图**：将字体、网格、密度、留白、视觉元素等要求转成具体设计，写入 `design-plan.md`。
4. **准备素材**：按构图需要生成无文字素材，或使用用户提供的图片；纯文字与图形页面可跳过生图。
5. **直接排版**：制作 1920×1080 HTML 页面，保留真实文字和独立对象。
6. **审阅实际页面**：检查可读性、内容正确性，以及完整风格提示词是否落实到最终视觉。
7. **导出**：可编辑 PPTX、整图 PPTX、PDF 和逐页 PNG。

Agent 根据完整文字规则设计构图，直接制作页面，并检查实际渲染结果。

## 输出

| 文件 | 说明 |
| --- | --- |
| `out/<名称>.pptx` | 可编辑文字、形状和独立图片，含备注 |
| `out/<名称>-images.pptx` | 实际排版渲染后的整页图片 |
| `out/<名称>.pdf` | 同一排版的 PDF |
| `out/png/`、`out/contact-sheet.jpg` | 逐页图片与总览 |

`--mode image` 只改变默认导出格式，仍由 Agent 构图并排版，再输出整图 PPTX 和 PDF。

## 使用

在支持 Skill 的 Agent 中直接描述需求，例如：

- 「用蓝黄等距风格（047）做 10 页 AI 客服升级方案，给管理层看」
- 「把年度总结做成 PPT，风格你来挑，重点突出结果」
- 「用新编辑野兽派（015）做产品宣传，标题要有海报感」

```bash
bash ppt-studio/scripts/ppt doctor --fonts
bash ppt-studio/scripts/ppt styles search 科技 蓝色
bash ppt-studio/scripts/ppt styles show 47 --both
bash ppt-studio/scripts/ppt init decks/demo --title "示例" --slides 8 --style 47
# Agent 阅读提示词，写方案并制作 slides/sNN.html
bash ppt-studio/scripts/ppt render decks/demo
bash ppt-studio/scripts/ppt export decks/demo
```

## 运行与安装

Python 3.10+ 和 Chrome / Edge；命令入口首次使用会准备独立 Python 环境。
仅需生成图片时才需要生图后端：优先用宿主工具，也支持 Codex CLI、OpenAI / Gemini API。
具体配置见 `references/image-backends.md`。图片数量由内容和风格决定。

本目录即技能本体，项目内 `.claude/skills/ppt-studio` 已链接到这里。需要全局使用时，
将该目录链接或复制到宿主的 skills 目录。`tools/pack.sh` 可打包。

## 文件组织

- `SKILL.md`：主工作流。
- `references/`：风格解读、Agent 构图、素材、排版、审阅和生图工具说明。
- `library/`：160 套完整风格规则及中文版本。
- `scripts/`：检索、新建、素材生成、渲染、导出与辅助工具。
- `assets/`：排版基础文件及 Lucide 图标。

依赖许可见 `NOTICE.md`。

## 展示案例：063 达达拼贴

用 PPT Studio 制作的 10 页 Skill 介绍，采用黑白摄影抠图、撕纸纹理、亮色色块和杂志式大标题，可作为排版与视觉风格的参考素材。

![第 1 页：PPT Studio](showcase/dada-collage/slide-01.jpg)

![第 2 页：输入与成果](showcase/dada-collage/slide-02.jpg)

![第 3 页：160 套风格目录](showcase/dada-collage/slide-03.jpg)

![第 4 页：完整的风格规格](showcase/dada-collage/slide-04.jpg)

![第 5 页：Agent 的逐页构图](showcase/dada-collage/slide-05.jpg)

![第 6 页：素材与排版分工](showcase/dada-collage/slide-06.jpg)

![第 7 页：完整制作流程](showcase/dada-collage/slide-07.jpg)

![第 8 页：可编辑交付](showcase/dada-collage/slide-08.jpg)

![第 9 页：交付文件](showcase/dada-collage/slide-09.jpg)

![第 10 页：下一份 PPT，从你的内容开始](showcase/dada-collage/slide-10.jpg)
