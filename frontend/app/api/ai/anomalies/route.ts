import OpenAI from "openai";

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const ANOMALY_FUNCTION: OpenAI.Chat.ChatCompletionTool = {
  type: "function",
  function: {
    name: "report_anomalies",
    description: "Report detected headcount anomalies from the dashboard data",
    parameters: {
      type: "object",
      properties: {
        anomalies: {
          type: "array",
          items: {
            type: "object",
            properties: {
              tab: {
                type: "string",
                enum: ["overall", "hrms-walk", "span", "spartan"],
                description: "Which dashboard tab this anomaly belongs to",
              },
              severity: {
                type: "string",
                enum: ["high", "medium", "low"],
                description: "Severity level of the anomaly",
              },
              title: {
                type: "string",
                description: "Short title (max 60 chars)",
              },
              explanation: {
                type: "string",
                description: "1-2 sentence explanation of why this is notable and what to investigate",
              },
            },
            required: ["tab", "severity", "title", "explanation"],
          },
          maxItems: 8,
          description: "List of detected anomalies, ordered by severity (high first)",
        },
      },
      required: ["anomalies"],
    },
  },
};

const SYSTEM = `You are an expert HR data analyst. Analyze the headcount dashboard data and identify genuine anomalies.
Focus on: unusual exit spikes, unexpected headcount drops/jumps, Spartan↔HRMS mismatches, payroll flags,
grade distribution shifts, and service line imbalances. Only flag real data issues, not normal fluctuations.`;

export async function POST(request: Request) {
  try {
    const { dashboardContext } = await request.json() as { dashboardContext: string };

    const response = await client.chat.completions.create({
      model: "gpt-4o",
      max_tokens: 1024,
      messages: [
        { role: "system", content: SYSTEM },
        {
          role: "user",
          content: `Analyze this BCG headcount data for anomalies:\n\n${dashboardContext}`,
        },
      ],
      tools: [ANOMALY_FUNCTION],
      tool_choice: "required",
    });

    const toolCall = response.choices[0]?.message?.tool_calls?.[0];
    if (!toolCall || toolCall.type !== "function") {
      return Response.json({ anomalies: [] });
    }

    const { anomalies } = JSON.parse(
      (toolCall as OpenAI.Chat.Completions.ChatCompletionMessageToolCall & { type: "function" }).function.arguments,
    ) as { anomalies: unknown[] };
    return Response.json({ anomalies: anomalies ?? [] });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    return new Response(JSON.stringify({ error: msg, anomalies: [] }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
