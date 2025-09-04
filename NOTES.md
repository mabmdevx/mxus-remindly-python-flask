#### Generate requirements.txt
```
pip freeze > requirements.txt
```

#### Rules by Recurrence Type
| Recurrence Type  | Start Date | End Date  | Notes                                                                 |
| ---------------- | ---------- | --------- | --------------------------------------------------------------------- |
| NONE (No repeat) | Optional   | Mandatory | End date is considered “due date”                                     |
| DAILY            | Mandatory  | Optional  | If end date omitted, recurrence is open-ended                         |
| WEEKLY           | Mandatory  | Optional  | User can select weekdays (MO, TU, etc.)                               |
| MONTHLY          | Mandatory  | Optional  | User can select day-of-month                                          |
| YEARLY           | Mandatory  | Optional  | Repeat every year on the same month/day                               |
| CUSTOM           | Mandatory  | Optional  | Full RRULE string is used; all recurrence options are derived from it |
