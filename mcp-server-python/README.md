

# Python Demo MCP Server

This repository contains a simple **MCP server** built with `FastMCP` in Python. It exposes both **tools** and **resources**.

- **Tools** are used for executable operations.
- **Resources** are used for read-only contextual data exposed through URIs.

## Exposed Operations

### Tools

#### `add(a: int, b: int) -> int`
Adds two integers and returns the result.

**Example**
```json
{
  "a": 5,
  "b": 7
}
````

**Response**

```text
12
```

#### `createPyramid(base: int) -> str`

Builds a text pyramid using `*` based on the given base size.

**Example**

```json
{
  "base": 4
}
```

**Response**

```text
    *
   * *
  * * *
 * * * *
```

> Note: this function should return `str`, not `int`, since it generates formatted text.

### Resources

#### `greeting://{name}`

Returns a personalized greeting.

**Example**

```text
greeting://Alice
```

**Response**

```text
Hello, Alice!
```

#### `greeting://person/{name}/age/{age}`

Returns a personalized greeting including name and age.

**Example**

```text
greeting://person/Alice/age/31
```

**Response**

```text
Hello Alice, you are 31!
```

## Design

This server follows a simple MCP design:

* Use **tools** for actions or calculations.
* Use **resources** for contextual, read-only data.

## Run

```bash
mcp dev server.py
```

