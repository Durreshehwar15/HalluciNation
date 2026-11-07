import { MASCOT, HEAD } from './assets.js'

// img  = full-body mascot (team cards)   head = avatar (feed, lists)
const TESTER = '/images/mascot5.png'
const WAITING = '/images/mas6.png'   // "Waiting for your approval" in the ticket list

export const AGENTS = [
  { name: 'Triage Agent', img: MASCOT.bunny, head: HEAD.bunny, text: 'Understands the report, finds the affected feature and opens the investigation task.' },
  { name: 'Code Investigation Agent', img: MASCOT.dog, head: HEAD.dog, text: 'Reads the code and logs and points to the likely root cause.' },
  { name: 'Fix Agent', img: MASCOT.dragon, head: HEAD.dragon, text: 'Writes a patch and explains why it should solve the problem.' },
  { name: 'Testing Agent', img: TESTER, head: TESTER, text: 'Runs the tests in an isolated Docker sandbox and reports the evidence.' },
  { name: 'Reviewer Agent', img: MASCOT.cat, head: HEAD.cat, text: 'Challenges the fix and either approves it or sends it back.' },
]

// Who is working on a ticket right now (used in the ticket list)
const INFO = {
  submitted: { head: HEAD.bunny, text: 'Waiting for the Triage Agent' },
  triage: { head: HEAD.bunny, text: 'Triage Agent is reading it' },
  investigating: { head: HEAD.dog, text: 'Investigation Agent is on the case' },
  fixing: { head: HEAD.dragon, text: 'Fix Agent is writing a patch' },
  testing: { head: TESTER, text: 'Testing Agent is running tests' },
  review: { head: HEAD.cat, text: 'Reviewer Agent is checking the fix' },
  awaiting_approval: { head: WAITING, text: 'Waiting for your approval' },
  approved: { emoji: '🎉', text: 'Approved' },
  pr_created: { emoji: '🎉', text: 'Pull request created' },
  merged: { emoji: '🎉', text: 'Merged!' },
  rejected: { head: HEAD.dragon, text: 'Sent back to the Fix Agent' },
}
export const statusInfo = (status) => INFO[status] || { emoji: '🎫', text: '' }