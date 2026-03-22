import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const SYSTEM = `You are an expert HR analytics assistant for BCG (Boston Consulting Group).
You have access to the dashboard's headcount data provided as context below.
Answer questions clearly and concisely about headcount, attrition, movements, spans, and anomalies.
Use numbers from the data. If asked something outside the data scope, say so honestly.
Format responses with markdown where helpful (bullet points, bold for numbers).`;

export async function POST(request: Request) {
  try {
    const { messages, dashboardContext } = await request.json() as {
      messages: Array<{ role: "user" | "assistant"; content: string }>;
      dashboardContext: string;
    };

    const systemPrompt = `${SYSTEM}\n\n---\n## Dashboard Data\n${dashboardContext}`;

    const stream = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 1024,
      system: systemPrompt,
      messages,
      stream: true,
    });

    const encoder = new TextEncoder();
    const readable = new ReadableStream({
      async start(controller) {
        for await (const event of stream) {
          if (
            event.type === "content_block_delta" &&
            event.delta.type === "text_delta"
          ) {
            const chunk = `data: ${JSON.stringify({ text: event.delta.text })}\n\n`;
            controller.enqueue(encoder.encode(chunk));
          }
        }
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
        controller.close();
      },
    });

    return new Response(readable, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    return new Response(JSON.stringify({ error: msg }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
