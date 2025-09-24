function CodeBlock(cb)
  return pandoc.RawBlock('latex',
    '\\begin{mycodeblock}\n' .. cb.text .. '\n\\end{mycodeblock}')
end