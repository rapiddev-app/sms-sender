package com.smsauto.companion;

import android.Manifest;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;

public class SmsCommandReceiver extends BroadcastReceiver {
    public static final String ACTION_SEND_SMS = "com.smsauto.companion.action.SEND_SMS";
    public static final String EXTRA_AUTH_TOKEN = "auth_token";
    public static final String EXTRA_REQUEST_ID = "request_id";
    public static final String EXTRA_PHONE = "phone";
    public static final String EXTRA_MESSAGE = "message";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || !ACTION_SEND_SMS.equals(intent.getAction())) {
            return;
        }

        String requestId = intent.getStringExtra(EXTRA_REQUEST_ID);
        String phone = intent.getStringExtra(EXTRA_PHONE);
        String message = intent.getStringExtra(EXTRA_MESSAGE);
        String authToken = intent.getStringExtra(EXTRA_AUTH_TOKEN);

        if (!StatusStore.ensureAuthToken(context).equals(authToken)) {
            StatusStore.appendStatus(context, requestId, phone, "AUTH_FAILED", "Invalid auth token");
            return;
        }
        if (isBlank(requestId) || isBlank(phone) || isBlank(message)) {
            StatusStore.appendStatus(context, requestId, phone, "FAILED", "Empty request payload");
            return;
        }
        if (context.checkSelfPermission(Manifest.permission.SEND_SMS)
                != PackageManager.PERMISSION_GRANTED) {
            StatusStore.appendStatus(
                    context,
                    requestId,
                    phone,
                    "FAILED",
                    "SEND_SMS permission is not granted"
            );
            return;
        }

        StatusStore.appendStatus(context, requestId, phone, "ACCEPTED", "");
        SmsDispatcher.send(context, requestId, phone, message);
    }

    private static boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }
}
