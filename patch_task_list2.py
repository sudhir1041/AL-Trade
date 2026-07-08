with open('TASK_LIST.md', 'r') as f:
    content = f.read()

content = content.replace('- [ ] Exchange adapter concrete implementations (Binance, Bybit, Mudrex)', '- [x] Exchange adapter concrete implementations (Binance, Bybit, Mudrex)')

with open('TASK_LIST.md', 'w') as f:
    f.write(content)
