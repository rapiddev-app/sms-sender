package com.smsauto.companion;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.telephony.SmsManager;

import java.util.ArrayList;

public final class SmsDispatcher {
    private SmsDispatcher() {
    }

    public static void send(Context context, String requestId, String phone, String message) {
        try {
            SmsManager smsManager = SmsManager.getDefault();
            ArrayList<String> parts = smsManager.divideMessage(message);
            if (parts.size() <= 1) {
                smsManager.sendTextMessage(
                        phone,
                        null,
                        message,
                        createStatusIntent(context, requestId, phone, SmsStatusReceiver.ACTION_SENT, 1),
                        createStatusIntent(
                                context,
                                requestId,
                                phone,
                                SmsStatusReceiver.ACTION_DELIVERED,
                                2
                        )
                );
            } else {
                smsManager.sendMultipartTextMessage(
                        phone,
                        null,
                        parts,
                        createStatusIntents(
                                context,
                                requestId,
                                phone,
                                SmsStatusReceiver.ACTION_SENT,
                                parts.size(),
                                100
                        ),
                        createStatusIntents(
                                context,
                                requestId,
                                phone,
                                SmsStatusReceiver.ACTION_DELIVERED,
                                parts.size(),
                                200
                        )
                );
            }
            StatusStore.appendStatus(context, requestId, phone, "QUEUED", "");
        } catch (IllegalArgumentException | SecurityException | UnsupportedOperationException error) {
            StatusStore.appendStatus(context, requestId, phone, "FAILED", error.toString());
        }
    }

    private static ArrayList<PendingIntent> createStatusIntents(
            Context context,
            String requestId,
            String phone,
            String action,
            int count,
            int offset
    ) {
        ArrayList<PendingIntent> intents = new ArrayList<>();
        for (int index = 0; index < count; index += 1) {
            intents.add(createStatusIntent(context, requestId, phone, action, offset + index));
        }
        return intents;
    }

    private static PendingIntent createStatusIntent(
            Context context,
            String requestId,
            String phone,
            String action,
            int requestCodeOffset
    ) {
        Intent intent = new Intent(context, SmsStatusReceiver.class);
        intent.setAction(action);
        intent.putExtra(SmsCommandReceiver.EXTRA_REQUEST_ID, requestId);
        intent.putExtra(SmsCommandReceiver.EXTRA_PHONE, phone);

        int requestCode = ((requestId + action).hashCode() & 0x7fffffff) % 100000
                + requestCodeOffset;
        return PendingIntent.getBroadcast(
                context,
                requestCode,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
    }
}
