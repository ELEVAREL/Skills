---
name: prompt-engineering
description: Optimize LLM prompts for better results. Use when writing system prompts, improving AI responses, designing prompt templates, or building AI-powered features.
---

# Prompt Engineering

Design effective prompts for LLMs.

## Core Principles

### 1. Be Specific and Explicit
- State exactly what you want, including format
- Provide constraints and boundaries
- Define what success looks like

### 2. Provide Context
- Role: "You are a senior backend engineer..."
- Task: "Review this code for security issues..."
- Format: "Return results as a JSON array..."
- Examples: Show input → expected output pairs

### 3. Use Structured Output
- Request JSON, XML, or markdown for parseable output
- Define the schema explicitly
- Include examples of the expected format

## Prompt Patterns

### Chain of Thought
```
Analyze this code for bugs. Think step by step:
1. First, identify what the code is supposed to do
2. Then, trace the execution path
3. Finally, identify any issues
```

### Few-Shot Examples
```
Classify these support tickets:

Input: "I can't log in to my account"
Category: Authentication

Input: "My payment was charged twice"
Category: Billing

Input: "The page loads very slowly"
Category: Performance

Input: "{user_ticket}"
Category:
```

### Role + Task + Format
```
You are a database performance expert.

Analyze the following SQL query and:
1. Identify performance issues
2. Suggest optimizations
3. Provide the optimized query

Format your response as:
## Issues
- [issue 1]

## Optimized Query
```sql
[query]
```

## Explanation
[why the changes help]
```

### Constrained Output
```
Extract the following fields from the text. Return ONLY valid JSON, no other text.

{
  "name": string,
  "email": string | null,
  "phone": string | null,
  "intent": "purchase" | "support" | "inquiry"
}
```

## Anti-Patterns

- **Vague instructions**: "Make it better" → "Improve readability by adding type annotations and docstrings"
- **Over-prompting**: Don't repeat the same instruction 5 ways
- **Conflicting instructions**: "Be concise" + "Explain in detail"
- **Missing context**: Assuming the model knows your codebase
- **No examples**: Expecting a specific format without showing it

## Testing Prompts

- Test with edge cases (empty input, very long input, adversarial input)
- Test with multiple models if targeting different providers
- Version control your prompts alongside code
- A/B test prompts when optimizing for quality
- Measure: accuracy, consistency, latency, cost
