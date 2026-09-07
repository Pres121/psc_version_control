library psc_update_service;

import 'package:flutter/material.dart';

import 'src/models/update_response.dart';
import 'src/services/update_client.dart';
import 'src/widgets/update_dialog.dart';

export 'src/models/update_response.dart';
export 'src/widgets/update_dialog.dart' show showPscUpdateDialog;

/// Simple static entrypoint so any PSC app can integrate in ~2 lines:
///
/// ```dart
/// PscUpdateService.configure(baseUrl: 'https://psc-update-api.onrender.com');
///
/// final update = await PscUpdateService.checkForUpdate(appKey: 'psc_notes');
/// if (context.mounted) {
///   await showPscUpdateDialog(context, appName: 'PSC Notes', info: update);
/// }
/// ```
class PscUpdateService {
  static String? _baseUrl;

  /// Call once at app startup (e.g. in main() or your app's root widget).
  static void configure({required String baseUrl}) {
    _baseUrl = baseUrl;
  }

  /// Offline-safe: never throws, never blocks app startup. Returns
  /// [PscUpdateInfo.none] if the backend can't be reached.
  static Future<PscUpdateInfo> checkForUpdate({required String appKey}) async {
    final baseUrl = _baseUrl;
    if (baseUrl == null) {
      throw StateError('PscUpdateService.configure() must be called before checkForUpdate()');
    }
    final client = PscUpdateClient(baseUrl: baseUrl);
    return client.checkForUpdate(appKey: appKey);
  }

  /// Convenience helper: checks for an update and shows the dialog if
  /// one is available, all in one call. Safe to call on every app launch.
  static Future<void> checkAndPromptIfNeeded(
    BuildContext context, {
    required String appKey,
    required String appName,
  }) async {
    final info = await checkForUpdate(appKey: appKey);
    if (!context.mounted) return;
    await showPscUpdateDialog(context, appName: appName, info: info);
  }
}
