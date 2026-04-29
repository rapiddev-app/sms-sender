package com.smsauto.companion;

import android.content.Context;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

public final class StatusStore {
    private static final String AUTH_TOKEN_FILE = "adb_token.txt";
    private static final String STATUS_LOG_FILE = "statuses.jsonl";

    private StatusStore() {
    }

    public static synchronized String ensureAuthToken(Context context) {
        File tokenFile = new File(context.getFilesDir(), AUTH_TOKEN_FILE);
        if (tokenFile.exists()) {
            try (BufferedReader reader = new BufferedReader(new FileReader(tokenFile))) {
                String token = reader.readLine();
                if (token != null && !token.trim().isEmpty()) {
                    return token.trim();
                }
            } catch (IOException ignored) {
                // Regenerate below.
            }
        }

        String token = UUID.randomUUID().toString();
        try (FileOutputStream stream = new FileOutputStream(tokenFile, false)) {
            stream.write(token.getBytes(StandardCharsets.UTF_8));
        } catch (IOException ignored) {
            // Receiver will reject commands if token cannot be persisted.
        }
        return token;
    }

    public static synchronized void appendStatus(
            Context context,
            String requestId,
            String phone,
            String state,
            String details
    ) {
        JSONObject payload = new JSONObject();
        try {
            payload.put("request_id", safe(requestId));
            payload.put("phone", safe(phone));
            payload.put("state", safe(state));
            payload.put("details", safe(details));
            payload.put("timestamp_ms", System.currentTimeMillis());
        } catch (JSONException ignored) {
            return;
        }

        File statusFile = new File(context.getFilesDir(), STATUS_LOG_FILE);
        String line = payload + "\n";
        try (FileOutputStream stream = new FileOutputStream(statusFile, true)) {
            stream.write(line.getBytes(StandardCharsets.UTF_8));
        } catch (IOException ignored) {
            // Status logging is best-effort; SMS callbacks must not crash the app.
        }
    }

    private static String safe(String value) {
        return value == null ? "" : value;
    }
}
