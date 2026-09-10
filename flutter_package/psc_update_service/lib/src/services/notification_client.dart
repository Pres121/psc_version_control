import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:package_info_plus/package_info_plus.dart';

/// Registers an FCM device token with the PSC update backend so the
/// server can subscribe it to the app's `app_key` topic.
///
/// This class does **not** depend on `firebase_messaging`. Obtain the
/// token in your host app, then pass it here.
class PscNotificationClient {
  final String baseUrl;
  final Duration timeout;

  PscNotificationClient({
    required this.baseUrl,
    this.timeout = const Duration(seconds: 6),
  });

  /// Returns `true` when the backend accepted the token.
  Future<bool> registerDevice({
    required String appKey,
    required String fcmToken,
  }) async {
    if (fcmToken.trim().isEmpty) return false;

    try {
      final packageInfo = await PackageInfo.fromPlatform();
      final platform = Platform.isIOS ? 'ios' : 'android';

      final response = await http
          .post(
            Uri.parse('$baseUrl/api/v1/notifications/devices/register'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'app_key': appKey,
              'platform': platform,
              'fcm_token': fcmToken,
              'app_version': packageInfo.version,
            }),
          )
          .timeout(timeout);

      if (response.statusCode != 200 && response.statusCode != 201) {
        _debugLog('Device register failed with HTTP ${response.statusCode}.');
        return false;
      }

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final registered = data['registered'] == true;
      if (!registered) {
        _debugLog('Device register rejected: ${data['reason']}');
      }
      return registered;
    } catch (error) {
      _debugLog('Device register could not complete: $error');
      return false;
    }
  }

  void _debugLog(String message) {
    assert(() {
      debugPrint('[PSC Notifications] $message');
      return true;
    }());
  }
}
