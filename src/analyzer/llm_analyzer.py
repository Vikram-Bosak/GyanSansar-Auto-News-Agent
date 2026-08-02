import json
import logging
import os
from openai import OpenAI

client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=os.getenv("NVIDIA_API_KEY", "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")
)

def generate_content_from_article(title, description):
    logging.info(f"Generating content for article: {title}")
    prompt = f"""
You are an expert copywriter for a viral Indian facts and news page like "Rochak Tathya".
Make the following news extremely engaging, mind-blowing, and curiosity-inducing.

Title: {title}
Description: {description}

Your task:
1. Choose ONE of these styles: "Meme Style", "Funny Style", "Emotional Style", "Sad Style", "Breaking News Style", "Fact Style".
2. Generate a hyper-engaging, dramatic 'headline' (MAX 10 WORDS). This must be strictly in HINDI (Devanagari script). Start with something like "क्या आप जानते हैं?", "हैरान करने वाली खबर!", or "यकीन नहीं होगा!".
3. Generate a viral 'hook_text' (1-2 sentences) to complement the headline. This must also be strictly in HINDI. Make the reader eager to know more.
4. Highlight 1 to 3 important keywords in the headline by wrapping them in asterisks like *this* to make them stand out.
5. **STRICT FACEBOOK POLICY CHECK:** Evaluate the article against Facebook Community Standards. If it contains "violence", "nudity_sexual", "hate_speech", "clickbait", "engagement_bait", "tragedy", or "politics_controversy", return a list of flags in the "safety_flags" array. Otherwise return [].

Respond STRICTLY in JSON format with four keys: "headline", "hook_text", "style", and "safety_flags". Do not include markdown formatting or backticks around the JSON.
"""
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            top_p=0.95,
            max_tokens=16384,
            extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":16384},
            stream=True
        )
        
        response_text = ""
        reasoning_text = ""
        for chunk in completion:
            if not chunk.choices:
                continue
            
            # Extract reasoning using getattr as requested
            reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
            if reasoning:
                reasoning_text += reasoning
                
            if chunk.choices[0].delta.content is not None:
                response_text += chunk.choices[0].delta.content
                
        logging.info(f"LLM Reasoning generated: {len(reasoning_text)} characters")
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        return json.loads(response_text.strip())
    except Exception as e:
        logging.error(f"LLM API failed: {e}")
        return {
            "headline": f"क्या आप जानते हैं? *{title}*!",
            "hook_text": "इंटरनेट पर यह खबर वायरल हो रही है!",
            "style": "Fact Style"
        }

def generate_facebook_caption(title):
    logging.info(f"Generating Facebook caption for: {title}")
    prompt = f"""
You are an expert social media manager for 'GyanSansar', a viral Indian facts page.
Write a highly engaging, click-worthy Facebook post caption for this news: {title}

Requirements:
- Keep it catchy, exciting, and short (3-4 sentences max).
- The caption must be written strictly in HINDI (Devanagari script).
- Include 3-4 relevant emojis.
- Include a very strong hook or dramatic question at the beginning.
- Include an engaging question at the end to drive comments.
- Include 5-6 relevant hashtags at the very bottom (like #HindiNews, #RochakTathya, #Trending, #GyanSansar).
- Do not include markdown formatting, just the raw text ready for Facebook.
"""
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            top_p=0.95,
            max_tokens=2048,
            extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":1024},
            stream=True
        )
        
        caption = ""
        reasoning_text = ""
        for chunk in completion:
            if not chunk.choices:
                continue
            reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
            if reasoning:
                reasoning_text += reasoning
            if chunk.choices[0].delta.content is not None:
                caption += chunk.choices[0].delta.content
                
        logging.info(f"Caption Reasoning generated: {len(reasoning_text)} characters")
        caption = caption.strip()
        
        if not caption:
            raise Exception("Empty response from LLM")
        return caption
    except Exception as e:
        logging.error(f"LLM caption generation failed: {e}")
        return (
            f"🚨 Hollywood Update! 🚨\n\n"
            f"{title}\n\n"
            f"Stay tuned for more updates! 👇\n"
            f"#HollywoodNews #CelebrityBuzz #Trending #Entertainment #News #CelebrityBuzzUSA"
        )
