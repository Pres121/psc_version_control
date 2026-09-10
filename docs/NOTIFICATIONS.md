# PSC Push Notifications (Flutter)

PSC release notifications are sent with **Firebase Cloud Messaging (FCM)**
to a topic named after each app's `app_key` (for example `psc_notes`).

Flow:

1. Flutter app gets an FCM token from Firebase.
2. App calls `POST /api/v1/notifications/devices/register`.
3. Backend stores the token and **subscribes it to the `app_key` topic**.
4. Admin sends a release notification from the dashboard → FCM topic push.

---

## 1. Dependencies (each PSC Flutter app)

```yaml
dependencies:
  firebase_core: ^3.8.0
  firebase_messaging: ^15.1.0
  psc_update_service:
    path: ../psc_update_service   # or your git path
```

Also add your `google-services.json` (Android) / `GoogleService-Info.plist` (iOS)
from the **same Firebase project** whose service-account JSON is set as
`FCM_CREDENTIALS_JSON` on the Render backend.

---

## 2. Configure once in `main.dart`

```dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:psc_update_service/psc_update_service.dart';

import 'firebase_options.dart'; // flutterfire configure

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  // Optional: handle data payload when app is killed/backgrounded.
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

  PscUpdateService.configure(
    baseUrl: 'https://psc-version-control.onrender.com',
  );

  runApp(const MyApp());
}
```

---

## 3. Register for notifications + update checks on first screen

Use the correct `appKey` per app:

| App            | appKey          |
|----------------|-----------------|
| PSC Notes      | `psc_notes`     |
| PSC Calendar   | `psc_calendar`  |
| PSC Savings    | `psc_savings`   |
| PSC Inventory  | `psc_inventory` |

```dart
import 'dart:io';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:psc_update_service/psc_update_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  static const appKey = 'psc_notes'; // change per app
  static const appName = 'PSC Notes';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await _setupNotifications();
      if (!mounted) return;
      await PscUpdateService.checkAndPromptIfNeeded(
        context,
        appKey: appKey,
        appName: appName,
      );
    });
  }

  Future<void> _setupNotifications() async {
    final messaging = FirebaseMessaging.instance;

    // iOS + Android 13+ permission prompt
    await messaging.requestPermission(alert: true, badge: true, sound: true);

    // Optional client-side topic subscribe (backend also subscribes server-side)
    await messaging.subscribeToTopic(appKey);

    final token = await messaging.getToken();
    if (token != null) {
      await PscUpdateService.registerForNotifications(
        appKey: appKey,
        fcmToken: token,
      );
    }

    // Refresh registration when FCM rotates the token
    FirebaseMessaging.instance.onTokenRefresh.listen((newToken) {
      PscUpdateService.registerForNotifications(
        appKey: appKey,
        fcmToken: newToken,
      );
    });

    // Foreground messages
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      final title = message.notification?.title ?? 'Update available';
      final body = message.notification?.body ?? '';
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$title\n$body')),
      );
    });

    // User tapped a notification (app opened from background)
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      // Navigate to an update / release notes screen if you want.
    });
  }

  @override
  Widget build(BuildContext context) => const Scaffold(/* ... */);
}
```

---

## 4. Android notes

In `android/app/src/main/AndroidManifest.xml`, ensure a default notification
channel if you customize one:

```xml
<meta-data
    android:name="com.google.firebase.messaging.default_notification_channel_id"
    android:value="psc_updates" />
```

Create that channel early in Dart if needed:

```dart
if (Platform.isAndroid) {
  // flutter_local_notifications can create the channel; optional for basic FCM.
}
```

---

## 5. iOS notes

- Enable **Push Notifications** + **Background Modes → Remote notifications**
  in Xcode.
- Upload an APNs key to the Firebase console for the same project.

---

## 6. Backend env check

On Render (or local `.env`):

```
FCM_CREDENTIALS_JSON={"type":"service_account",...}
```

Without this, device register still stores the token, but topic subscribe /
send will not work until credentials are set.

---

## 7. Verify end-to-end

1. Launch the Flutter app → Logs page should show `device_register` + IP.
2. Launch / resume the app → Logs page should show `update_check` + IP.
3. Publish a release in the dashboard.
4. Open **Notifications** → send to that app/release.
5. Device receives the FCM push (and history shows `sent`).
