package com.smsauto.companion;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.telephony.SmsManager;

public class SmsStatusReceiver extends BroadcastReceiver {
    public static final String ACTION_SENT = "com.smsauto.companion.action.SMS_SENT";
    public static final String ACTION_DELIVERED = "com.smsauto.companion.action.SMS_DELIVERED";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null) {
            return;
        }

        String requestId = intent.getStringExtra(SmsCommandReceiver.EXTRA_REQUEST_ID);
        String phone = intent.getStringExtra(SmsCommandReceiver.EXTRA_PHONE);
        String action = intent.getAction();

        if (ACTION_SENT.equals(action)) {
            StatusStore.appendStatus(context, requestId, phone, sentState(), sentDetails());
        } else if (ACTION_DELIVERED.equals(action)) {
            boolean delivered = getResultCode() == Activity.RESULT_OK;
            StatusStore.appendStatus(
                    context,
                    requestId,
                    phone,
                    delivered ? "DELIVERED" : "DELIVERY_FAILED",
                    delivered ? "" : "Delivery result code: " + getResultCode()
            );
        }
    }

    private String sentState() {
        return getResultCode() == Activity.RESULT_OK ? "SENT" : "SEND_FAILED";
    }

    private String sentDetails() {
        return switch (getResultCode()) {
            case Activity.RESULT_OK -> "";
            case SmsManager.RESULT_ERROR_GENERIC_FAILURE -> "Generic failure";
            case SmsManager.RESULT_ERROR_NO_SERVICE -> "No service";
            case SmsManager.RESULT_ERROR_NULL_PDU -> "Null PDU";
            case SmsManager.RESULT_ERROR_RADIO_OFF -> "Radio off";
            default -> "Send result code: " + getResultCode();
        };
    }
}
