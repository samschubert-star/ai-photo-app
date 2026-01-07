import { NextRequest, NextResponse } from "next/server";

// This API route handles the virtual try-on request
// It's designed to work with various AI providers (Replicate, Hugging Face, etc.)

export async function POST(request: NextRequest) {
  try {
    const { personImage, clothingImage } = await request.json();

    if (!personImage || !clothingImage) {
      return NextResponse.json(
        { error: "Both person image and clothing image are required" },
        { status: 400 }
      );
    }

    // Check for API key
    const apiKey = process.env.REPLICATE_API_TOKEN;

    if (!apiKey) {
      // Demo mode - return a simulated response for testing
      console.log("No API key configured - running in demo mode");

      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 3000));

      // In demo mode, return the original person image with a notice
      // This allows users to test the UI flow without an API key
      return NextResponse.json({
        success: true,
        resultImage: personImage,
        demo: true,
        message: "Demo mode - Set REPLICATE_API_TOKEN for real AI processing"
      });
    }

    // Call Replicate API for virtual try-on
    // Using IDM-VTON model which is excellent for virtual try-on
    const replicateResponse = await fetch("https://api.replicate.com/v1/predictions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json",
        "Prefer": "wait"
      },
      body: JSON.stringify({
        version: "c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
        input: {
          garm_img: clothingImage,
          human_img: personImage,
          garment_des: "clothing item"
        }
      })
    });

    if (!replicateResponse.ok) {
      const errorData = await replicateResponse.json();
      console.error("Replicate API error:", errorData);
      return NextResponse.json(
        { error: "AI processing failed. Please try again." },
        { status: 500 }
      );
    }

    const prediction = await replicateResponse.json();

    // If the prediction is still processing, we need to poll for results
    if (prediction.status === "starting" || prediction.status === "processing") {
      // Poll for results
      const resultUrl = prediction.urls?.get;
      let result = prediction;
      let attempts = 0;
      const maxAttempts = 60; // 60 seconds timeout

      while (
        (result.status === "starting" || result.status === "processing") &&
        attempts < maxAttempts
      ) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        const pollResponse = await fetch(resultUrl, {
          headers: {
            "Authorization": `Bearer ${apiKey}`,
          }
        });
        result = await pollResponse.json();
        attempts++;
      }

      if (result.status === "succeeded" && result.output) {
        const outputImage = Array.isArray(result.output) ? result.output[0] : result.output;
        return NextResponse.json({
          success: true,
          resultImage: outputImage
        });
      } else if (result.status === "failed") {
        return NextResponse.json(
          { error: result.error || "AI processing failed" },
          { status: 500 }
        );
      } else {
        return NextResponse.json(
          { error: "Processing timed out. Please try again." },
          { status: 504 }
        );
      }
    }

    // Direct result (when using Prefer: wait)
    if (prediction.status === "succeeded" && prediction.output) {
      const outputImage = Array.isArray(prediction.output) ? prediction.output[0] : prediction.output;
      return NextResponse.json({
        success: true,
        resultImage: outputImage
      });
    }

    return NextResponse.json(
      { error: "Unexpected response from AI service" },
      { status: 500 }
    );

  } catch (error) {
    console.error("Try-on API error:", error);
    return NextResponse.json(
      { error: "An error occurred during processing" },
      { status: 500 }
    );
  }
}
