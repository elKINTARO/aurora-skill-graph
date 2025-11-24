RANKS = {
    0: '🌱 Новачок',
    50: '👶 Студент',
    150: '🔨 Підмайстер',
    300: '🛠️ Спеціаліст',
    600: '🧠 Експерт',
    1000: '🧙‍♂️ Архітектор',
    2000: '👑 Легенда',
}


def get_rank_info(total_xp):
    current_rank = '🌱 Новачок'
    next_rank = None
    xp_for_next = None

    thresholds = sorted(RANKS.keys())

    for i, threshold in enumerate(thresholds):
        if total_xp >= threshold:
            current_rank = RANKS[threshold]
            if i + 1 < len(thresholds):
                xp_for_next = thresholds[i + 1]
                next_rank = RANKS[xp_for_next]
            else:
                next_rank = 'Max Level'
                xp_for_next = total_xp
        else:
            break

    if next_rank == 'Max Level':
        progress_percent = 100
    else:
        progress_percent = int((total_xp / xp_for_next) * 100) if xp_for_next else 0

    return {
        'current_rank': current_rank,
        'next_rank': next_rank,
        'xp_needed': xp_for_next - total_xp if xp_for_next else 0,
        'progress_percent': progress_percent
    }