package com.smsauto.companion;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final int REQUEST_SEND_SMS = 1001;

    private TextView permissionStatus;
    private TextView tokenStatus;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        StatusStore.ensureAuthToken(this);
        buildLayout();
        refreshState();
    }

    @Override
    protected void onResume() {
        super.onResume();
        refreshState();
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode,
            String[] permissions,
            int[] grantResults
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_SEND_SMS) {
            refreshState();
        }
    }

    private void buildLayout() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        int padding = 32;
        root.setPadding(padding, padding, padding, padding);

        TextView title = new TextView(this);
        title.setText("SMS Auto Companion");
        title.setTextSize(22);
        root.addView(title);

        permissionStatus = new TextView(this);
        permissionStatus.setTextSize(16);
        root.addView(permissionStatus);

        tokenStatus = new TextView(this);
        tokenStatus.setTextSize(14);
        root.addView(tokenStatus);

        Button requestButton = new Button(this);
        requestButton.setText("Grant SMS permission");
        requestButton.setOnClickListener(view -> requestPermissions(
                new String[] {Manifest.permission.SEND_SMS},
                REQUEST_SEND_SMS
        ));
        root.addView(requestButton);

        setContentView(root);
    }

    private void refreshState() {
        boolean granted = checkSelfPermission(Manifest.permission.SEND_SMS)
                == PackageManager.PERMISSION_GRANTED;
        permissionStatus.setText(granted ? "SEND_SMS: granted" : "SEND_SMS: not granted");
        tokenStatus.setText("ADB token: " + StatusStore.ensureAuthToken(this));
    }
}
