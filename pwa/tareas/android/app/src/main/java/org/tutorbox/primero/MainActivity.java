package org.tutorbox.primero;

import android.app.Activity;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import java.io.IOException;
import java.util.Locale;

/** Q'uq' Matemáticas: the Primero web app, packaged with its files so it works with no internet. */
public class MainActivity extends Activity {

    // Android reserves this host for apps serving their own files. A real https origin (not
    // file://) is what lets the ES module scripts load and localStorage keep the progress.
    private static final String ORIGIN = "https://appassets.androidplatform.net/";

    private WebView web;
    private TextToSpeech tts;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        tts = new TextToSpeech(this, status -> {
            // Latin-American Spanish first; plain Spanish if the phone lacks that voice.
            if (status == TextToSpeech.SUCCESS
                    && tts.setLanguage(new Locale("es", "US")) < TextToSpeech.LANG_AVAILABLE) {
                tts.setLanguage(new Locale("es"));
            }
        });

        web = new WebView(this);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setMediaPlaybackRequiresUserGesture(false);
        // WebView has no speechSynthesis; audio.js calls this instead (window.AndroidTTS).
        web.addJavascriptInterface(new Speech(), "AndroidTTS");
        web.setWebViewClient(new AssetClient());
        setContentView(web);

        if (savedInstanceState == null) {
            web.loadUrl(ORIGIN + "index.html");
        } else {
            web.restoreState(savedInstanceState);
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        web.saveState(outState);
    }

    @Override
    public void onBackPressed() {
        // The app routes by #hash, so Back walks its screens before leaving.
        if (web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        tts.shutdown();
        web.destroy();
        super.onDestroy();
    }

    private class Speech {
        @JavascriptInterface
        public void speak(String text, float rate, float pitch) {
            tts.setSpeechRate(rate);
            tts.setPitch(pitch);
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "kuk");
        }
    }

    /** Serves ORIGIN from the APK's assets (pwa/tareas/primero/public); nothing else loads. */
    private class AssetClient extends WebViewClient {
        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            return !request.getUrl().toString().startsWith(ORIGIN);
        }

        @Override
        public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
            if (!request.getUrl().toString().startsWith(ORIGIN)) {
                return null;
            }
            String path = request.getUrl().getPath().substring(1);
            if (path.isEmpty()) {
                path = "index.html";
            }
            try {
                return new WebResourceResponse(mimeType(path), "utf-8", getAssets().open(path));
            } catch (IOException e) {
                return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found", null, null);
            }
        }
    }

    // Module scripts refuse to run without a JavaScript MIME type, so map it explicitly.
    private static String mimeType(String path) {
        switch (path.substring(path.lastIndexOf('.') + 1)) {
            case "html": return "text/html";
            case "js": return "text/javascript";
            case "css": return "text/css";
            case "json": return "application/json";
            case "svg": return "image/svg+xml";
            case "png": return "image/png";
            case "woff2": return "font/woff2";
            default: return "application/octet-stream";
        }
    }
}
