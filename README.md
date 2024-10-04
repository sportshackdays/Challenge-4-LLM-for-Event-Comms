# Challenge-4-LLM-for-Event-Comms

## Data Explanation

Each item in the **data array** represents a single conversation between customer service and a customer. Within each conversation, messages are listed in order in the **messages array**.

### Labels for Messages

We provide two labels for each message:

1. **Category**
   - Possible values:
     - `"request"`
     - `"question"`
     - `"spam"`
     - `null` (used for outgoing emails)

2. **Preferred Reaction**
   - Possible values:
     - `"respond"`
     - `"forward_to_human"`
     - `"nothing"`

### Personal Data Placeholders

Personal data is replaced by placeholders enclosed in brackets, such as `[placeholder_id]`. In any response message, it is required to use the same placeholders with the correct IDs.