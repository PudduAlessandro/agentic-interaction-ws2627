## Actions to classify

| Action | Reaction | Justification |
|--------|----------|---------------|
| Read the appointments of a day | alone | Since checking for appointments is a read-only call, the agent shouldn't have to ask for approval |
| Look up the weather | alone | Also read-only so it's fine |
| Search train connections | alone | Checking for connections should not need approval until attempting to purchase a ticket |
| Read notes | alone | Just reading in itself is fine, however, confidential notes should ask for approval depending on context |
| Create a personal block in the calendar | approval | Since creating a personal block might affect future appointments, the agent should ask for approval |
| Reschedule an appointment with other attendees | approval | Similar reason to "Create a personal block" |
| Book a train ticket | approval | Making a purchase should require approval after showing what exactly is going to be bought |
| Send a message to third parties | approval | Might depend on the recipient but before sending out messages in my name I should be able to see the message about to be sent |
| Create a note | alone | Might also depend on who is able to see the resulting notes, but creating notes without approval for oneself should be fine |
| Delete a note | approval | Deleting information should always require approval since it is usually irreversible |

### (My) Rule in one Sentence
For this set of actions, the agent should always ask for approval before doing anything that is **not** read-only.

### Observations
- Depending on the wording used during the requests (like “Get me to the workshop visit…”), the agent acted on its own too much without asking for approval first, unless we told it to stop.
- Since tool calls were called out by the agent, it was clear what it was working on at all times
- Because only the agent was looking at the raw data before summarizing it at its own discretion, some information got omitted depending on the request
- The more precise the request was (containing parameters such as dates), the better the returned information
