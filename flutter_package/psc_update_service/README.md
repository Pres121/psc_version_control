# psc_update_service

Reusable in-app update checker for all PSC Flutter applications.

## Install

Add as a local/path or git dependency in each app's `pubspec.yaml`:

```yaml
dependencies:
  psc_update_service:
    path: ../psc_update_service
    # or: git: { url: https://github.com/psc/psc-update-service, path: psc_update_service }
```

## Usage (PSC Notes example)

```dart
import 'package:flutter/material.dart';
import 'package:psc_update_service/psc_update_service.dart';

void main() {
  PscUpdateService.configure(baseUrl: 'https://psc-update-api.onrender.com');
  runApp(const MyApp());
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    // Runs after first frame; never blocks app startup, never throws
    // if the backend is unreachable.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      PscUpdateService.checkAndPromptIfNeeded(
        context,
        appKey: 'psc_notes',
        appName: 'PSC Notes',
      );
    });
  }

  @override
  Widget build(BuildContext context) => const Scaffold(/* ... */);
}
```

Repeat the same pattern in PSC Calendar, PSC Savings, and PSC Inventory,
swapping only `appKey` and `appName` (`psc_calendar`, `psc_savings`,
`psc_inventory`). New PSC apps only need to register their `app_key` in
the admin dashboard and add these same two lines - no backend changes
required.

## Offline-first behavior

- Network calls run against a short timeout (4s by default).
- Any failure (offline, DNS error, backend down, non-200 response) is
  caught internally and treated as "no update available".
- The last successful check is cached in `SharedPreferences` so a
  brief network blip doesn't drop update visibility entirely.
- The host app's UI and functionality are never blocked or delayed by
  the update check.
