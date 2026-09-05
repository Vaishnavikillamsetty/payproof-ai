import pathlib

p = pathlib.Path('src/utils.ts')
text = p.read_text(encoding='utf-8')

old_format = """/** Format a number as USD. */
export function formatAmount(n: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(n)
}"""

new_format = """/** Format a number as currency based on the provided code. */
export function formatAmount(n: number, currency: string = 'USD'): string {
  // Use the INR currency format consistently (e.g. ₹45.00).
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
  })
  return `${formatter.format(n)} ${currency.toUpperCase()}`
}"""

text = text.replace(old_format, new_format)
p.write_text(text, encoding='utf-8')
