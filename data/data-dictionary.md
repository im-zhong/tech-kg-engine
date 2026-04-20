
# 科技知识图谱 · 数据字典

> **版本**：v1.0  
> **更新日期**：2026-04-20  
> **数据性质**：本数据集为项目演示所用的虚拟数据，字段规范对齐第三方数据提供方标准，真实数据由第三方按此结构提供。

---

## 概览

| 序号 | 文件名 | 数据类型 | 记录数 | 字段数 |
|------|--------|---------|--------|--------|
| 1 | `scholars.json` | 学者（人才） | 15 | 18 |
| 2 | `papers_cn.json` | 中文论文 | 12 | 64 |
| 3 | `papers_en.json` | 外文论文 | 38 | 67 |
| 4 | `patents.json` | 专利 | 28 | 20 |
| 5 | `projects_domestic.json` | 国内项目 | 22 | 15 |
| 6 | `projects_foreign.json` | 国外项目 | 5 | 15 |
| 7 | `institutions_domestic.json` | 国内机构 | 5 | 17 |
| 8 | `institutions_foreign.json` | 国外机构 | 3 | 23 |

---

## 1. scholars.json · 学者表

> 记录科技学者的基础信息、学术影响力指标、组织与工作经历。

| 字段名 | 中文说明 | 类型 | 示例 |
|--------|---------|------|------|
| `scholarId` | 学者唯一ID | string | `"sch_a1b2c3d4"` |
| `nameZh` | 中文姓名 | string | `"张伟"` |
| `nameEn` | 英文姓名 | string | `"Zhang Wei"` |
| `gender` | 性别 | string | `"male"` / `"female"` |
| `birth` | 出生年份 | number | `1978` |
| `professional_title_level` | 当前职称级别 | string | `"教授"` |
| `hIndex` | H指数 | number | `42` |
| `citationNums` | 被引总数 | number | `18650` |
| `paperNums` | 论文数量 | number | `87` |
| `scholarOrgNameZh` | 所属机构中文名 | string | `"北京大学"` |
| `scholarOrgNameEn` | 所属机构英文名 | string | `"Peking University"` |
| `orgId` | 所属机构ID（关联机构表） | string | `"inst_pku_cs"` |
| `researchDirection` | 研究方向 | string[] | `["知识图谱", "深度学习"]` |
| `workExperienceZh` | 工作经历（中文，非结构化文本） | string | `"2010年—至今，北京大学计算机科学与技术系，教授"` |
| `workExperienceEn` | 工作经历（英文，非结构化文本） | string | `"2010–present, Professor, Peking University"` |
| `educationBackgroundZh` | 教育背景（中文） | string | `"2001年至2006年就读于…"` |
| `educationBackgroundEn` | 教育背景（英文） | string | `"From 2001 to 2006…"` |

> **说明**：`workExperienceZh` / `workExperienceEn` 为自然语言文本，与第三方数据提供方格式保持一致。模块4（同事关系推理）在开发阶段由后端对该文本进行结构化解析，解析结果不存入原始数据。

---

## 2. papers_cn.json · 中文论文表

> 记录中文期刊论文的文献信息、作者机构关联、期刊评价指标。

### 文献基础信息

| 字段名 | 中文说明 | 类型 |
|--------|---------|------|
| `paper_id` | 文献唯一ID | string |
| `zh_name` | 论文中文题目 | string |
| `zh_abstract` | 中文摘要 | string |
| `doi` | DOI唯一标识符 | string |
| `keywords` | 关键词列表 | string[] |
| `cover_date_start` | 发表时间 | string |
| `paper_url` | 论文原始链接 | string |
| `paper_type` | 文献类型 | string |
| `volume` | 卷号 | string |
| `issue` | 期号 | string |
| `first_page` | 起始页码 | string |
| `last_page` | 末尾页码 | string |
| `location` | 发表机构所在地经纬度 | string |
| `content` | 论文全文 | string |

### 引用与被引

| 字段名 | 中文说明 | 类型 |
|--------|---------|------|
| `citation_nums` | 被引用文献数量 | number |
| `citation_content` | 被引用文献内容 | string |
| `citation_ids` | 被引用文献ID列表 | string[] |
| `reference_nums` | 引用文献数量 | number |
| `reference_content` | 引用文献内容 | string |
| `reference_ids` | 引用文献ID列表 | string[] |
| `relevant` | 相关文献 | string |

### 作者与机构

| 字段名 | 中文说明 | 类型 |
|--------|---------|------|
| `authors` | 作者信息列表 | object[] |
| `authors[].id` | 作者ID（关联学者表） | string |
| `authors[].role` | 作者角色（如通讯作者等） | string |
| `authors[].personinfo.fullName` | 作者中文全名 | string |
| `authors[].organizationInfos[].id` | 所属机构ID | string |

### 期刊基础信息

| 字段名 | 中文说明 | 类型 |
|--------|---------|------|
| `journal_name_zh` | 期刊/顶会名（中文） | string |
| `journal_name_en` | 期刊/顶会名（英文） | string |
| `journal_type` | 期刊/顶会类别/预印本 | string |
| `journal_abbreviation` | 简称 | string |
| `journal_alias` | 期刊/顶会别名 | string |
| `country` | 国家 | string |
| `issn` | ISSN | string |
| `eissn` | EISSN | string |
| `iscn` | 国内刊号 | string |
| `publication_id` | 关联出版刊物信息 | string |
| `publication_name` | 出版刊物中文名称 | string |
| `publication_type` | 出版刊物类型 | string |
| `publisher` | 出版商 | string |
| `publisher_id` | 出版商id | string |

### 出版信息

| 字段名 | 中文说明 | 类型 |
|--------|---------|------|
| `zh_description` | 期刊/顶会描述 | string |
| `format` | 开本 | string |
| `founding_time` | 创刊时间 | string |
| `language` | 语种 | string |
| `postal_code` | 邮发代号 | string |
| `chief_editor` | 主编 | string |
| `organizer` | 主办单位 | string |
| `publisher_place` | 出版地 | string |
| `publication_cycle` | 出版周期 | string |
| `mobile` | 期刊出版商电话 | string |
| `address` | 期刊出版商地址 | string |
| `jn_official` | 期刊官网 | string |

### 期刊评价与指标

| 字段名 | 中文说明 | 类型 |
|--------|---------|------|
| `impact_factor` | 影响因子 | number |
| `jcr_zone` | JCR 分区 | string |
| `scope_zone` | 中科院分区：分区 | string |
| `scope` | 中科院分类：大类学科 | string |
| `journal_db_str` | 收录数据库 | string |
| `open_access` | 是否OA | boolean |
| `warning_flag` | 是否预警 | boolean |
| `top_flag` | 是否顶刊 | boolean |
| `review` | 是否为综述性期刊 | boolean |
| `annual_publication` | 年文章数 | number |
| `cite_nums` | 被引用量 | number |
| `fund_nums` | 基金论文数 | number |
| `paper_nums` | 出版论文数 | number |
| `download_nums` | 下载量 | number |
| `award` | 获奖情况 | string |
| `partition` | 期刊分类来源及分区 | object |
| `partition.source` | 期刊分类来源（SCI/WOS/CCF/JCR） | string |
| `partition.subject_level` | 期刊学科分类级别 | string |
| `partition.partition` | 期刊学科分类分区（Q1/Q2/A类B类等） | string |

---

## 3. papers_en.json · 外文论文表

> 与中文论文结构基本一致，以下列出差异字段。

| 差异字段 | 中文说明 | 类型 |
|--------|---------|------|
| `en_name` | 论文英文题目（替代 zh_name） | string |
| `en_abstract` | 英文摘要（替代 zh_abstract） | string |
| `en_description` | 期刊英文描述（替代 zh_description） | string |
| `authors[].personinfo.englishFullName` | 作者英文全名（替代 fullName） | string |
| `publication_en_name` | 出版刊物英文名称 | string |
| `name_abbr` | 期刊英文简写 | string |
| `language_classify` | 语种分类 | string |
| `funds` | 基金 | string |
| `graphical_abstract` | 摘要图 | string |
| `review_period` | 平均审稿周期 | string |
| `self_rate` | 自引率 | number |
| `number_of_cites` | 国人占比 | number |
| `layout_cost` | 版面费 | number |

> 其余字段与 `papers_cn.json` 相同，请参考第2节。

---

## 4. patents.json · 专利表

> 记录专利的基础信息、发明人、法律状态等。

| 字段名 | 中文说明 | 类型 |
|--------|---------|------|
| `id` | 专利ID（与DOCDB兼容） | string |
| `title_Localized` | 专利标题 | string |
| `abstract_Localized` | 专利摘要 | string |
| `application_Number` | 专利申请号 | string |
| `publication_Number` | 专利公布号 | string |
| `application_Kind` | 专利申请类型（A/U/P/W/F/T） | string |
| `filing_Date` | 申请日期 | string |
| `publication_Date` | 发布日期 | string |
| `filing_Year` | 申请年份 | number |
| `publication_Year` | 发布年份 | number |
| `ipc` | 国际专利分类 | string |
| `cpc` | 合作专利分类 | string |
| `landscapes` | 技术领域分类 | string |
| `keywords` | 关键词 | string[] |
| `assignee` | 受让人/申请人 | string |
| `current_Assignee` | 当前受让人/申请人 | string |
| `inventor` | 发明人（原始文本） | string |
| `inventor_Harmonized` | 发明者信息列表 | object[] |
| `inventor_Harmonized[].name` | 发明者姓名 | string |
| `citation_Nums` | 专利引用数量 | number |
| `status` | 专利状态 | string |

---

## 5. projects_domestic.json · 国内项目表

> 记录国内科研项目基本信息及关联成果。

| 字段名 | 中文说明 | 类型 |
|--------|---------|------|
| `project_id` | 项目编号 | string |
| `title` | 项目名称 | string |
| `project_source` | 项目来源（如国家重点研发计划） | string |
| `funded_institution` | 项目受资助机构 | string |
| `funded_amount` | 受资助金额 | number |
| `project_level` | 项目级别（国家级/省级等） | string |
| `project_domain` | 项目领域/研究方向 | string |
| `approval_time` | 立项时间 | string |
| `research_period` | 研究期限（月数） | number |
| `project_host` | 项目主持人姓名 | string |
| `keywords` | 关键词 | string[] |
| `abstract` | 项目标书摘要 | string |
| `participants` | 参与者列表 | object[] |
| `participants[].scholar_id` | 参与者学者ID（关联学者表） | string |
| `participants[].name` | 参与者姓名 | string |
| `participants[].role` | 参与者角色 | string |
| `paper_ids` | 项目产出论文ID列表 | string[] |
| `patent_ids` | 项目产出专利ID列表 | string[] |

---

## 6. projects_foreign.json · 国外项目表

> 与国内项目表结构完全相同，记录国际合作科研项目。参考第5节。

---

## 7. institutions_domestic.json · 国内机构表

> 记录国内高校、科研院所的基础信息。

| 字段名 | 中文说明 | 类型 |
|--------|---------|------|
| `id` | 机构唯一ID | string |
| `name_cn` | 机构中文名称 | string |
| `org_en` | 机构英文名称 | string |
| `alias` | 机构别名列表 | string[] |
| `type` | 机构类型（高校/科研院所等） | string |
| `country_name` | 所在国家 | string |
| `country_code` | 国家代码 | string |
| `province` | 所在省份/区 | string |
| `city` | 所在城市 | string |
| `address` | 机构地址 | string |
| `postal_code` | 邮政编码 | string |
| `phone` | 联系电话 | string |
| `fax` | 传真号码 | string |
| `email` | 电子邮箱 | string |
| `website` | 官方网站 | string |
| `external_id` | 外部唯一注册码（如ROR） | string |
| `affiliates_name` | 下属机构列表 | object[] |
| `affiliates_name[].id` | 下属机构ID | string |
| `affiliates_name[].name` | 下属机构名称 | string |
| `affiliates_name[].local_name` | 下属机构本地名称/英文名 | string |
| `affiliates_name[].parent_id` | 父机构ID | string |

---

## 8. institutions_foreign.json · 国外机构表

> 在国内机构表基础上，额外包含以下字段。

| 额外字段 | 中文说明 | 类型 |
|--------|---------|------|
| `description_en` | 机构英文简介 | string |
| `description_ch` | 机构中文简介 | string |
| `is_service` | 是否为科技服务机构 | boolean |
| `latitude` | 机构地理位置纬度 | number |
| `longitude` | 机构地理位置经度 | number |
| `image` | 机构logo图片文件 | string |

> 其余字段与 `institutions_domestic.json` 相同，请参考第7节。

---

## 表间关联关系

```
scholars.orgId              → institutions_domestic/foreign.id

papers_cn/en.authors[].id        → scholars.scholarId
papers_cn/en.authors[].organizationInfos[].id → institutions_domestic/foreign.id

patents.inventor_Harmonized[].name  → scholars.nameZh（姓名匹配）

projects_domestic/foreign.participants[].scholar_id → scholars.scholarId
projects_domestic/foreign.paper_ids   → papers_cn/en.paper_id
projects_domestic/foreign.patent_ids  → patents.id
```

---

## 模块支撑说明

| 业务模块 | 所需数据表 |
|---------|-----------|
| 模块1：科技专家直接关系 | scholars · papers_cn · papers_en · patents |
| 模块2：科技单节点间接关系 | scholars · papers_cn · papers_en · patents |
| 模块3：科技两点合作成果 | scholars · papers_cn · papers_en · patents · projects_domestic · projects_foreign |
| 模块4：科技专家同事关系 | scholars（workExperienceZh 解析） · institutions_domestic · institutions_foreign |
