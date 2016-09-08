ITEM_FORMAT = '''
\\newpage
\\stepurl{{{item[step_url]}}}
\\stepstatistics{{{item[step_id]:.0f}}}{{{item[difficulty]:.2f}}}{{{item[discrimination]:.2f}}}{{{item[item_total_corr]:.2f}}}{{{item[n_people]:.0f}}}{{{item[step_type]}}}

\\begin{{question}}
{item[question]}
\\end{{question}}
'''

OPTION_FORMAT = '\\option{{{label}}}{{{name}}}{{{difficulty}}} \n'