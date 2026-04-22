\# 琴房数据分析工具



从微信云开发导出预约数据，生成经营报表与可视化图表。



\## 快速开始



```bash

cd analytics

pip install -r requirements.txt

python src/export\_data.py

```



\## 输出



| Sheet | 内容 |

|-------|------|

| 个人统计 | 每个用户的总时长、预约次数、活跃天数 |

| 房间利用 | 各房间利用率对比 |

| 时段热度 | 24小时预约分布 |

| 核销明细 | 完整原始数据 |

| 爽约名单 | 预约未到店用户 |



\## 技术栈



\- Python 3.6+

\- pandas / openpyxl / matplotlib

