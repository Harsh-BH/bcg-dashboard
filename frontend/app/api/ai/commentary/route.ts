import OpenAI from "openai";

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const SYSTEM = `You are a senior HR analytics consultant at BCG writing an executive headcount commentary.
Write in a professional, data-driven tone. Use numbers precisely. Highlight trends, risks, and notable movements.
Structure your response in markdown with these sections:
## Executive Summary
## Headcount Movement
## Bucket Analysis
## Anomalies & Watch Items

Keep each section concise (3-5 bullet points). Use bold for key numbers.`;

export async function POST(request: Request) {
  try {
    const { dashboardContext } = await request.json() as { dashboardContext: string };

    const stream = await client.chat.completions.create({
      model: "gpt-4o",
      max_tokens: 1500,
      messages: [
        { role: "system", content: SYSTEM },
        {
          role: "user",
          content: `Generate a Month-over-Month headcount commentary for the following BCG HR data:\n\n${dashboardContext}`,
        },
      ],
      stream: true,
    });

    const encoder = new TextEncoder();
    const readable = new ReadableStream({
      async start(controller) {
        for await (const chunk of stream) {
          const text = chunk.choices[0]?.delta?.content ?? "";
          if (text) {
            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify({ text })}\n\n`)
            );
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
