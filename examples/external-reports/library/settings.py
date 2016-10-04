ITEM_FORMAT = '''
\\newpage
\\stepurl{{{item[step_url]}}}
\\stepstatistics{{{item[step_id]:.0f}}}{{{item[difficulty]:.2f}}}{{{item[discrimination]:.2f}}}{{{item[item_total_corr]:.2f}}}{{{item[n_people]:.0f}}}{{{item[step_type]}}}

\\begin{{question}}
{item[question]}
\\end{{question}}
'''

OPTION_FORMAT = '\\option{{{label}}}{{{name}}}{{{difficulty}}} \n'


STEP_FORMAT = '''
\\newpage
\\stepurl{{{step_url}}}
\\section*{{Видео~{step_id:.0f}}}

\\includegraphics[scale=0.8]{{generated/step_{step_id:.0f}.png}}
'''
MIN_VIDEO_LENGTH = 5