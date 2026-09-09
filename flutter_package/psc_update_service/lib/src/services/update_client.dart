import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/update_response.dart';

/// Reusable update-check client for all PSC Flutter apps.
///
/// Offline-first by design: any network failure, timeout, or backend
/// error is swallowed and treated as "no update available" so the host
/// app always continues to function normally.
class PscUpdateClient {
  final String baseUrl;
  final Duration timeout;

  PscUpdateClient({
    required this.baseUrl,
    this.timeout = const Duration(seconds: 4),
  });

  static const _cacheKey = 'psc_update_service_last_check';

  Future<PscUpdateInfo> checkForUpdate({required String appKey}) async {
    try {
      final packageInfo = await PackageInfo.fromPlatform();
      final platform = Platform.isIOS ? 'ios' : 'android';
      final version = packageInfo.version;
      final buildNumber = int.tryParse(packageInfo.buildNumber) ?? 0;

      final response = await http
          .post(
            Uri.parse('$baseUrl/api/v1/updates/check'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'app_key': appKey,
              'platform': platform,
              'version': version,
              'build_number': buildNumber,
            }),
          )
          .timeout(timeout);

      if (response.statusCode != 200) {
        _debugLog('Update check failed with HTTP ${response.statusCode}.');
        return await _fallbackToCache();
      }

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final info = PscUpdateInfo.fromJson(data);
      await _cacheResult(info);
      return info;
    } catch (error) {
      _debugLog('Update check could not complete: $error');
      // Network unavailable, timeout, DNS failure, malformed response, etc.
      // Never let an update check crash or block the host app.
      return await _fallbackToCache();
    }
  }

  Future<void> _cacheResult(PscUpdateInfo info) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_cacheKey, jsonEncode(info.toJson()));
    } catch (_) {
      // Caching is best-effort only.
    }
  }

  /// If we can't reach the backend, optionally fall back to the last
  /// successful check rather than surfacing an error. If nothing is
  /// cached, we simply report "no update" and let the app continue.
  Future<PscUpdateInfo> _fallbackToCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final cached = prefs.getString(_cacheKey);
      if (cached != null) {
        return PscUpdateInfo.fromJson(jsonDecode(cached) as Map<String, dynamic>);
      }
    } catch (_) {
      // Ignore cache read errors too.
    }
    return PscUpdateInfo.none();
  }

  void _debugLog(String message) {
    // The production behavior remains offline-safe, but debug builds expose
    // enough information to identify an incorrect URL or unavailable API.
    assert(() {
      debugPrint('[PSC Update] $message');
      return true;
    }());
  }
}
