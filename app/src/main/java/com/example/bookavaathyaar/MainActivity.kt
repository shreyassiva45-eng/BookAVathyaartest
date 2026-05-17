package com.example.bookavaathyaar

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.enableEdgeToEdge
import android.webkit.WebView
import android.webkit.WebViewClient

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // Create the WebView and configure it perfectly
        val webView = WebView(this)

        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true // Essential for modern responsive styling & layouts
            useWideViewPort = true
            loadWithOverviewMode = true
        }

        // Force links and redirects to open inside the app frame
        webView.webViewClient = WebViewClient()

        // Set the webView as the main screen layout
        setContentView(webView)

        // Load the URL directly so it renders themes and images properly
        webView.loadUrl("https://bookavaathyaartest.onrender.com")
    }
}

