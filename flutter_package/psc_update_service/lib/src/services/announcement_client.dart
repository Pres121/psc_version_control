import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../models/announcement.dart';

/// Fetches the latest in-app announcement for an app (no Firebase).
class PscAnnouncementClient {
  final String baseUrl;
  final Duration timeout;

  PscAnnouncementClient({
    required this.baseUrl,
    this.timeout = const Duration(seconds: 4),
  });

  static String _dismissedKey(String appKey) =>
      'psc_announcement_dismissed_$appKey';

  /// Returns the active announcement, or `null` if none / already dismissed / offline.
  Future<PscAnnouncement?> checkForAnnouncement({required String appKey}) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/v1/announcements/check'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'app_key': appKey}),
          )
          .timeout(timeout);

      if (response.statusCode != 200) {
        _debugLog('Announcement check failed with HTTP ${response.statusCode}.');
        return null;
      }

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      if (data['has_announcement'] != true || data['announcement'] == null) {
        return null;
      }

      final announcement = PscAnnouncement.fromJson(
        data['announcement'] as Map<String, dynamic>,
      );

      final prefs = await SharedPreferences.getInstance();
      final dismissedId = prefs.getString(_dismissedKey(appKey));
      if (dismissedId == announcement.id) {
        return null;
      }
      return announcement;
    } catch (error) {
      _debugLog('Announcement check could not complete: $error');
      return null;
    }
  }

  /// Call after the user dismisses the dialog so it won't show again.
  Future<void> markDismissed({
    required String appKey,
    required String announcementId,
  }) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_dismissedKey(appKey), announcementId);
    } catch (_) {
      // Best-effort only.
    }
  }

  void _debugLog(String message) {
    assert(() {
      debugPrint('[PSC Announcement] $message');
      return true;
    }());
  }
}
