import ddlc from '../syntax/ddlc.json'

/* A code block is the kitty window of this repository, dark on either schema, so one Shiki theme
   taken from the syntax table's dark column serves both sides of a deck */
export default () => ({ themes: { light: ddlc, dark: ddlc } })
