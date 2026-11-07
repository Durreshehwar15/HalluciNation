export const STEPS = [
  {
    n: 1, title: 'Report a bug', color: '#f06292', kind: 'antenna', link: '/submit', cta: 'Open the form',
    short: 'Describe what went wrong in the New Ticket form.',
    long: [
      'Click New ticket in the top menu.',
      'Write a short title, e.g. “Payment page crashes on invalid coupon”.',
      'Describe what you did and what happened. The more detail, the better the agents can investigate.',
      'Optionally paste error logs, then press Submit ticket.',
    ],
  },
  {
    n: 2, title: 'Watch the agents work', color: '#7b4fb3', kind: 'fuzzy', link: '/tickets', cta: 'See tickets',
    short: 'Follow each agent as it investigates, fixes, tests and reviews.',
    long: [
      'After submitting you land on the ticket page automatically.',
      'The progress bar shows the stage: Triage, Investigation, Fix, Testing, Review, Human Approval.',
      'The Agent activity feed shows each message and handoff between agents, with the evidence they attach (files, logs, test output).',
      'The page refreshes by itself every 2 seconds. You do not need to reload.',
    ],
  },
  {
    n: 3, title: 'Review the patch', color: '#b8c4cc', kind: 'robot', link: '/tickets', cta: 'Open a ticket',
    short: 'Check the code change, the test results and the reviewer’s verdict.',
    long: [
      'When all agents are done the status becomes “awaiting approval” and a Review patch button appears.',
      'In the code diff, green lines were added and red lines were removed.',
      'Test results show how many tests passed, including the new test for your bug.',
      'The Reviewer verdict explains why the reviewer agent accepted the fix.',
    ],
  },
  {
    n: 4, title: 'Approve or request changes', color: '#f0b98a', kind: 'hat', link: '/tickets', cta: 'Go to tickets',
    short: 'Nothing is merged until a human says yes.',
    long: [
      'Press Approve & create PR to create the GitHub pull request.',
      'Or write feedback and press Request changes to send the ticket back to the agents.',
      'Once approved, a View pull request link appears on the ticket.',
      'Agents can never merge code by themselves. You are always in control.',
    ],
  },
]

export const STATUSES = [
  ['submitted', 'Your ticket was received.'],
  ['triage', 'The Triage Agent is reading the report.'],
  ['investigating', 'The Code Investigation Agent is looking for the cause.'],
  ['fixing', 'The Fix Agent is writing a patch.'],
  ['testing', 'The Testing Agent is running tests in a sandbox.'],
  ['review', 'The Reviewer Agent is checking the fix and the evidence.'],
  ['awaiting_approval', 'Your turn! Review the patch and decide.'],
  ['approved', 'You approved the fix.'],
  ['pr_created', 'The GitHub pull request was created.'],
  ['merged', 'The fix has been merged.'],
  ['rejected', 'Changes were requested; the agents will try again.'],
]

export const FAQ = [
  ['Nothing is happening on my ticket. What now?', 'The agents work one after another, so a stage can take a little while. The page updates automatically. If the progress bar has not moved for several minutes, tell the team member who runs Switch.'],
  ['Can the agents merge code without me?', 'No. The pull request is only created after you press Approve & create PR.'],
  ['What happens if the tests fail?', 'The Reviewer Agent sends the fix back to the Fix Agent, and the ticket does not reach the approval step until the evidence is good.'],
  ['What is Switch?', 'Switch is the collaboration layer that connects the agents. They share a team room, hand work to each other, share evidence and challenge each other’s results. The activity feed on the ticket page shows that conversation.'],
  ['Why do I see sample data?', 'Demo mode uses built-in sample tickets so the website works without the backend. The team can turn it off to use the real system.'],
]
