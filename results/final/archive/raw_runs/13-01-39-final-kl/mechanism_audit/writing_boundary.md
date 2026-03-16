# Writing Boundary

## Strong
- `L2H14->MLP11`: candidate ingress edge from query-side reader into the early tool writer
- `MLP11->MLP16`: candidate relay edge from early tool write into the shared late relay
- `MLP16->L24H6`: candidate late relay edge inside the query-conditioned branch
- `L21H12->MLP27`: carries schema/protocol-conditioned signal into the final late writer
- `L16H4->MLP17`: passes no-tool-biased user-side evidence into the no-tool writer
- `MLP17->L23H6`: passes no-tool-biased written state into the late suppressive relay

## Weak
- `MLP11`: evidence suggests candidate early tool-favoring writer downstream of the query-side reader
- `MLP16`: evidence suggests shared late relay/writer that transports upstream tool-biased state toward the output-adjacent region
- `L21H12`: evidence suggests reads schema/protocol availability cues and sends them to the late tool writer
- `MLP27`: evidence suggests late writer that converts schema-conditioned state into a tool-call-favoring output direction
- `L16H4`: evidence suggests reads no-tool / ordinary-answer evidence from the user-side prompt and feeds the no-tool chain
- `MLP17`: evidence suggests writes a no-tool-favoring residual state inside the suppression chain
- `L23H6`: evidence suggests late suppressive relay that carries no-tool-biased state toward the output
- `L24H6`: evidence suggests late relay/writer that helps carry tool-biased state into the final output region

## Do Not Write Strongly
- unified mode switcher
- arbitration zone
- decision boundary module
- default conservative branch
- `L2H14` strong functional claim
