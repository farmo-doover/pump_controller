
1) Do these schedules have an end date?

2) Are these schedules going to update outside our ui? Can we get a webhook back to Doover in that case?

3) RE: add_schedule endpoint, add optional schedule_id field so that client and specify an id

4) Current get_schedules call seems to return invalid device despite accepting create schedule call

5) 33355533355533 isn't valid (api responds with invalid regex, as less than 15 characters)

6) Can we add editing frequency to the update endpoint?

7) Update endpoint also causes updated item to change frequency to 'once'. Could just implement in client that we delete and recreate instead of update

8) Webhook from scheduling server to notify doover of an updated schedule??

9) (Not Critical) Personal preference Would be to Nest most API data one layer further to provide more options in the future
