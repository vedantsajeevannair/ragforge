# API examples

All examples use `curl` against a local server on port 8000.

```bash
# Register (the first account becomes admin) and keep the token
TOKEN=$(curl -s -X POST localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username": "alice", "password": "a-long-password"}' | jq -r .access_token)
AUTH="Authorization: Bearer $TOKEN"

# Upload a file into a collection, visible only to you and admins
curl -s -H "$AUTH" -F file=@handbook.pdf -F collection=hr -F visibility=private \
  localhost:8000/documents

# Large files return 202 with a job id; poll until done
curl -s -H "$AUTH" localhost:8000/jobs/1

# Ranked passages, with highlight offsets
curl -s -H "$AUTH" -H 'Content-Type: application/json' localhost:8000/search \
  -d '{"query": "parental leave", "k": 5, "collection": "hr"}'

# A cited answer
curl -s -H "$AUTH" -H 'Content-Type: application/json' localhost:8000/ask \
  -d '{"query": "How many weeks of parental leave are there?"}'

# A follow-up that reuses the previous question
curl -s -H "$AUTH" -H 'Content-Type: application/json' localhost:8000/ask \
  -d '{"query": "Does it apply to contractors?",
       "previous_questions": ["How many weeks of parental leave are there?"]}'

# Stream the answer as server-sent events
curl -N -H "$AUTH" -H 'Content-Type: application/json' localhost:8000/ask/stream \
  -d '{"query": "Summarise the leave policy"}'
```

The stream sends `event: sources` (retrieved passages), many `event: token`, then
`event: done` with the final answer, citations, confidence and timings. On a provider
error it sends `event: error` instead of `done`.

## Python

```python
import httpx

api = httpx.Client(base_url="http://localhost:8000")
token = api.post("/auth/login", json={"username": "alice",
                                      "password": "a-long-password"}).json()["access_token"]
api.headers["Authorization"] = f"Bearer {token}"

answer = api.post("/ask", json={"query": "What is the notice period?"}).json()
print(answer["answer"])
for c in answer["citations"]:
    print(f"  [{c['number']}] {c['source']}")
```
