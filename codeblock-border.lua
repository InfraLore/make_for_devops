function CodeBlock(cb)
  return pandoc.RawBlock('latex',
    '\\Needspace{8\\baselineskip}\n\\begin{mycodeblock}\n' .. cb.text .. '\n\\end{mycodeblock}')
    -- '\\begin{mycodeblock}\n' .. cb.text .. '\n\\end{mycodeblock}')
end