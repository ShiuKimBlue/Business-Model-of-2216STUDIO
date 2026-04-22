#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import load_json_data, parse_date_range, ensure_dir


DEFAULT_DATA_PATH = os.path.join('data', 'bookings.json')
DEFAULT_OUTPUT_DIR = 'output'
BUSINESS_HOURS_PER_DAY = 10

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def analyze_bookings(df, start_date, end_date, output_dir=DEFAULT_OUTPUT_DIR):
    output_dir = ensure_dir(output_dir)
    period_label = f"{start_date}_至_{end_date}"
    
    df['date'] = pd.to_datetime(df['date'])
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    df_period = df.loc[mask].copy()
    
    if len(df_period) == 0:
        print(f"⚠️ {period_label} 期间无数据")
        return None
    
    df_checked = df_period[df_period['status'] == 'checked-in'].copy()
    
    print(f"\n{'='*60}")
    print(f"🎹 2216 Studio 经营数据报告")
    print(f"📅 {start_date} 至 {end_date}")
    print(f"{'='*60}")
    
    user_stats = _analyze_users(df_checked)
    room_stats = _analyze_rooms(df_checked)
    hour_dist = _analyze_hours(df_checked)
    no_show_df, no_show_rate = _analyze_no_shows(df_period)
    
    excel_path = _generate_excel(
        user_stats, room_stats, hour_dist,
        df_checked, no_show_df,
        output_dir, period_label
    )
    
    chart_path = _generate_charts(
        df_checked, room_stats, hour_dist,
        output_dir, period_label
    )
    
    _print_summary(df_checked, df_period, no_show_rate, user_stats)
    
    return {'excel': excel_path, 'chart': chart_path}


def _analyze_users(df_checked):
    stats = df_checked.groupby('displayName').agg({
        'duration': 'sum',
        'room': 'count',
        'date': 'nunique'
    }).rename(columns={
        'duration': '总时长(小时)',
        'room': '预约次数',
        'date': '活跃天数'
    })
    return stats.sort_values('总时长(小时)', ascending=False)


def _analyze_rooms(df_checked):
    stats = df_checked.groupby('room').agg({
        'duration': 'sum',
        'date': 'nunique'
    })
    stats['理论可用时长'] = stats['date'] * BUSINESS_HOURS_PER_DAY
    stats['利用率(%)'] = (stats['duration'] / stats['理论可用时长'] * 100).round(1)
    return stats.sort_values('利用率(%)', ascending=False)


def _analyze_hours(df_checked):
    df_checked['hour'] = df_checked['timeSlot'].str[:2].astype(int)
    return df_checked.groupby('hour').size().sort_values(ascending=False)


def _analyze_no_shows(df_period):
    no_show = df_period[
        (df_period['status'] == 'booked') &
        (df_period['checkInAt'].isna() | (df_period['checkInAt'] == ''))
    ]
    rate = len(no_show) / len(df_period) * 100 if len(df_period) > 0 else 0
    return no_show, rate


def _generate_excel(user_stats, room_stats, hour_dist,
                     df_checked, no_show_df,
                     output_dir, period_label):
    excel_path = os.path.join(output_dir, f"周报_{period_label}.xlsx")
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        user_stats.to_excel(writer, sheet_name='个人统计')
        room_stats.to_excel(writer, sheet_name='房间利用')
        hour_dist.to_frame('预约人次').to_excel(writer, sheet_name='时段热度')
        
        detail_cols = ['date', 'room', 'timeSlot', 'displayName', 'duration', 'note']
        df_checked[detail_cols].to_excel(writer, sheet_name='核销明细', index=False)
        
        if len(no_show_df) > 0:
            no_show_df[['date', 'room', 'timeSlot', 'displayName', 'note']].to_excel(
                writer, sheet_name='爽约名单', index=False
            )
    
    return excel_path


def _generate_charts(df_checked, room_stats, hour_dist, output_dir, period_label):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'2216 Studio 周报\n({period_label})', fontsize=14)
    
    room_stats['利用率(%)'].plot(kind='bar', ax=axes[0,0], color='#87CEEB')
    axes[0,0].set_title('各房间利用率', fontsize=11)
    axes[0,0].set_ylabel('利用率(%)')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    hour_dist.sort_index().plot(kind='line', ax=axes[0,1],
                                marker='o', color='#FF7F50')
    axes[0,1].set_title('24小时预约热度', fontsize=11)
    axes[0,1].set_xlabel('小时')
    axes[0,1].set_ylabel('人次')
    axes[0,1].grid(True, alpha=0.3)
    
    top10 = user_stats['总时长(小时)'].sort_values().tail(10)
    top10.plot(kind='barh', ax=axes[1,0], color='#90EE90')
    axes[1,0].set_title('消费时长Top 10', fontsize=11)
    axes[1,0].set_xlabel('小时')
    
    daily = df_checked.groupby('date').size()
    daily.plot(kind='line', ax=axes[1,1], marker='s', color='#9370DB')
    axes[1,1].set_title('每日预约趋势', fontsize=11)
    axes[1,1].set_ylabel('人次')
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    chart_path = os.path.join(output_dir, f"图表_{period_label}.png")
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return chart_path


def _print_summary(df_checked, df_period, no_show_rate, user_stats):
    total_hours = df_checked['duration'].sum()
    active_users = df_checked['displayName'].nunique()
    
    print(f"\n📊 核心指标")
    print(f"   总核销时长：{total_hours:.1f} 小时")
    print(f"   活跃用户：{active_users} 人")
    print(f"   爽约率：{no_show_rate:.1f}%")
    
    if len(user_stats) > 0:
        print(f"\n🏆 本周Top 1：{user_stats.index[0]}（{user_stats.iloc[0]['总时长(小时)']}小时）")
    
    print(f"\n✅ 报表已生成，请查看 output/ 目录")


def main():
    print("🎹 2216 Studio 数据分析系统")
    print("=" * 60)
    
    try:
        df = load_json_data(DEFAULT_DATA_PATH)
        print(f"📥 加载完成：共 {len(df)} 条记录")
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        sys.exit(1)
    
    start_date, end_date = parse_date_range(days=7)
    result = analyze_bookings(df, start_date, end_date)
    
    if result:
        print(f"\n{'='*60}")
        print("📅 月度汇总...")
        from datetime import datetime
        today = datetime.now().date()
        month_dir = ensure_dir(os.path.join(DEFAULT_OUTPUT_DIR, '月度报告'))
        analyze_bookings(df, str(today.replace(day=1)), str(today), output_dir=month_dir)


if __name__ == '__main__':
    main()