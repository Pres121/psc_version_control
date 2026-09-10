library psc_update_service;

import 'package:flutter/material.dart';

import 'src/models/announcement.dart';
import 'src/models/update_response.dart';
import 'src/services/announcement_client.dart';
import 'src/services/notification_client.dart';
import 'src/services/update_client.dart';
import 'src/widgets/announcement_dialog.dart';
import 'src/widgets/update_dialog.dart';

export 'src/models/announcement.dart';
export 'src/models/update_response.dart';
export 'src/services/announcement_client.dart';
export 'src/services/notification_client.dart';
export 'src/widgets/announcement_dialog.dart' show showPscAnnouncementDialog;
export 'src/widgets/update_dialog.dart' show showPscUpdateDialog;

/// Simple static entrypoint so any PSC app can integrate in ~2 lines.
class PscUpdateService {
  static String? _baseUrl;

  /// Call once at app startup (e.g. in main() or your app's root widget).
  static void configure({required String baseUrl}) {
    _baseUrl = baseUrl;
  }

  static String get _requireBaseUrl {
    final baseUrl = _baseUrl;
    if (baseUrl == null) {
      throw StateError('PscUpdateService.configure() must be called first');
    }
    return baseUrl;
  }

  /// Offline-safe: never throws, never blocks app startup. Returns
  /// [PscUpdateInfo.none] if the backend can't be reached.
  static Future<PscUpdateInfo> checkForUpdate({required String appKey}) async {
    final client = PscUpdateClient(baseUrl: _requireBaseUrl);
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

  /// Fetches the latest in-app announcement (no Firebase).
  /// Returns `null` if none, already dismissed, or offline.
  static Future<PscAnnouncement?> checkForAnnouncement({
    required String appKey,
  }) async {
    final client = PscAnnouncementClient(baseUrl: _requireBaseUrl);
    return client.checkForAnnouncement(appKey: appKey);
  }

  /// Checks for an in-app announcement and shows a dialog if one exists.
  /// Marks it dismissed after the user closes the dialog.
  static Future<void> checkAndShowAnnouncementIfNeeded(
    BuildContext context, {
    required String appKey,
  }) async {
    final client = PscAnnouncementClient(baseUrl: _requireBaseUrl);
    final announcement = await client.checkForAnnouncement(appKey: appKey);
    if (announcement == null || !context.mounted) return;

    await showPscAnnouncementDialog(context, announcement: announcement);
    await client.markDismissed(
      appKey: appKey,
      announcementId: announcement.id,
    );
  }

  /// Update check + in-app announcement (in that order). No Firebase.
  static Future<void> checkUpdatesAndAnnouncements(
    BuildContext context, {
    required String appKey,
    required String appName,
  }) async {
    await checkAndPromptIfNeeded(context, appKey: appKey, appName: appName);
    if (!context.mounted) return;
    await checkAndShowAnnouncementIfNeeded(context, appKey: appKey);
  }

  /// Optional FCM device register (only if you also want system pushes).
  static Future<bool> registerForNotifications({
    required String appKey,
    required String fcmToken,
  }) async {
    final client = PscNotificationClient(baseUrl: _requireBaseUrl);
    return client.registerDevice(appKey: appKey, fcmToken: fcmToken);
  }
}
