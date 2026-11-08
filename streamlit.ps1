param(
    [Parameter(ValueFromRemainingArguments=$true)]
    $Args
)
python -m streamlit $Args

