sessions = {}

MEMBERS = ['แบม', 'ชาติ', 'นาจา', 'กัญ', 'อาร์ม', 'มิ้ว', 'พิม', 'อ้าย']

DEFAULT_SECTIONS = [
    'Roll out / ลงพื้นที่',
    'งานวิจัย',
    'ประชุม',
    'งานค้าง / ติดปัญหา',
]

NEXT_CMDS = ['ถัดไป', 'next', 'ข้าม', 'skip']
DONE_CMDS = ['เสร็จ', 'done', 'จบ', 'finish']
START_CMDS = ['/เริ่ม', '/start', 'เริ่ม', 'start']


def handle_message(user_id, text):
    low = text.lower().strip()

    if user_id not in sessions or low in START_CMDS:
        sessions[user_id] = _new_session()
        return _ask_member()

    s = sessions[user_id]
    state = s['state']

    if state == 'ASK_MEMBER':
        return _process_member(user_id, text)
    elif state == 'ASK_WEEK':
        return _process_week(user_id, text)
    elif state == 'ASK_DATE_START':
        return _process_date_start(user_id, text)
    elif state == 'ASK_DATE_END':
        return _process_date_end(user_id, text)
    elif state == 'IN_SECTION':
        return _process_section(user_id, text)

    return 'พิมพ์ /เริ่ม เพื่อกรอกแผนงานใหม่ครับ 🌿'


def _new_session():
    return {
        'state': 'ASK_MEMBER',
        'member': None,
        'week': None,
        'date_start': None,
        'date_end': None,
        'sections': [{'name': s, 'items': []} for s in DEFAULT_SECTIONS],
        'current_section': 0,
    }


def _ask_member():
    lines = ['สวัสดีครับ! 👋 กรอกแผนงานสัปดาห์นี้กันเลย\n']
    lines.append('เลือกชื่อหรือพิมพ์ชื่อได้เลยครับ:')
    for i, m in enumerate(MEMBERS):
        lines.append(f'{i+1}. {m}')
    return '\n'.join(lines)


def _process_member(user_id, text):
    s = sessions[user_id]
    if text.strip().isdigit():
        idx = int(text.strip()) - 1
        if 0 <= idx < len(MEMBERS):
            s['member'] = MEMBERS[idx]
        else:
            return 'กรุณาเลือกหมายเลข 1–8 ครับ'
    else:
        matched = next((m for m in MEMBERS if m in text), text.strip())
        s['member'] = matched
    s['state'] = 'ASK_WEEK'
    return f'ยินดีต้อนรับ {s["member"]} 🌿\n\nสัปดาห์ที่เท่าไหร่ครับ? (พิมพ์ตัวเลข เช่น 26)'


def _process_week(user_id, text):
    s = sessions[user_id]
    s['week'] = text.strip()
    s['state'] = 'ASK_DATE_START'
    return 'วันเริ่มต้นของสัปดาห์ครับ? (เช่น 23/6)'


def _process_date_start(user_id, text):
    s = sessions[user_id]
    s['date_start'] = text.strip()
    s['state'] = 'ASK_DATE_END'
    return 'วันสิ้นสุดของสัปดาห์ครับ? (เช่น 27/6)'


def _process_date_end(user_id, text):
    s = sessions[user_id]
    s['date_end'] = text.strip()
    s['state'] = 'IN_SECTION'
    return _start_section(user_id)


def _start_section(user_id):
    s = sessions[user_id]
    idx = s['current_section']

    if idx >= len(s['sections']):
        return _generate_markdown(user_id)

    sec_name = s['sections'][idx]['name']
    total = len(s['sections'])
    return (
        f'📌 หัวข้อ {idx+1}/{total}: {sec_name}\n\n'
        f'พิมพ์แต่ละรายการ เช่น:\n"23/6: แจกไม้ป่า ชนแดน"\n\n'
        f'คำสั่ง:\n'
        f'• "ถัดไป" → ไปหัวข้อต่อไป\n'
        f'• "เสร็จ" → จบและสร้าง Markdown'
    )


def _process_section(user_id, text):
    s = sessions[user_id]
    low = text.lower().strip()

    if low in DONE_CMDS:
        return _generate_markdown(user_id)

    if low in NEXT_CMDS:
        s['current_section'] += 1
        return _start_section(user_id)

    s['sections'][s['current_section']]['items'].append(text.strip())
    count = len(s['sections'][s['current_section']]['items'])
    return f'✅ บันทึกแล้ว ({count} รายการ)\nพิมพ์รายการถัดไป หรือ "ถัดไป" เพื่อเปลี่ยนหัวข้อครับ'


def _generate_markdown(user_id):
    s = sessions[user_id]

    md = f'# รายงานประจำสัปดาห์ที่ {s["week"]} — {s["member"]}\n'
    md += f'**ช่วงวันที่:** {s["date_start"]} – {s["date_end"]} 2569\n\n---\n'

    for sec in s['sections']:
        if not sec['items']:
            continue
        md += f'\n## {sec["name"]}\n\n'
        md += '| วันที่ | รายละเอียด |\n|--------|------------|\n'
        for item in sec['items']:
            if ':' in item:
                parts = item.split(':', 1)
                md += f'| {parts[0].strip()} | {parts[1].strip()} |\n'
            else:
                md += f'| — | {item} |\n'

    md += '\n## หมายเหตุ\n'

    del sessions[user_id]

    return (
        f'✅ Markdown พร้อมแล้วครับ {s["member"]}!\n\n'
        f'```\n{md}```\n\n'
        f'คัดลอกข้อความด้านบนส่งให้อาร์มใน LINE ได้เลยครับ 🌿\n\n'
        f'พิมพ์ /เริ่ม เพื่อกรอกใหม่'
    )
