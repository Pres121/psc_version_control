import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/update_response.dart';

Future<void> _openUpdateUrl(BuildContext context, String url) async {
  final uri = Uri.tryParse(url);
  if (uri == null || !uri.hasScheme) {
    _showUpdateMessage(context, 'Invalid update link from server.');
    return;
  }

  try {
    // Do not gate on canLaunchUrl — on Android it often returns false for https
    // even when launchUrl works. Try launch directly.
    final launched = await launchUrl(
      uri,
      mode: LaunchMode.externalApplication,
    );
    if (!launched) {
      _showUpdateMessage(
        context,
        'Could not open the update page. Check your browser or try again.',
      );
    }
  } catch (error) {
    assert(() {
      debugPrint('[PSC Update] launchUrl failed: $error');
      return true;
    }());
    _showUpdateMessage(
      context,
      'Could not open the update page. Check your internet connection.',
    );
  }
}

void _showUpdateMessage(BuildContext context, String message) {
  if (!context.mounted) return;
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text(message)),
  );
}

/// Shows the appropriate PSC update dialog for [info].
/// Does nothing if no update is available.
Future<void> showPscUpdateDialog(
  BuildContext context, {
  required String appName,
  required PscUpdateInfo info,
}) async {
  if (!info.updateAvailable && !info.updateRequired) return;

  await showDialog(
    context: context,
    barrierDismissible: !info.updateRequired,
    builder: (context) => PopScope(
      canPop: !info.updateRequired,
      child: AlertDialog(
        title: Text(
          info.updateRequired ? '⚠️ Update Required' : '🚀 New version available',
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              info.updateRequired
                  ? 'Your version of $appName is no longer supported.\n\n'
                      'Please update to continue using the application.'
                  : '$appName ${info.latestVersion ?? ''} is now available.',
            ),
            if (!info.updateRequired && info.releaseNotes.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text("What's new:", style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              ...info.releaseNotes.map((note) => Text('• $note')),
            ],
          ],
        ),
        actions: [
          if (!info.updateRequired)
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Later'),
            ),
          FilledButton(
            onPressed: () async {
              final url = info.updateUrl?.trim();
              if (url == null || url.isEmpty) {
                _showUpdateMessage(
                  context,
                  'No download link yet. Ask your admin to upload the app build.',
                );
                return;
              }

              await _openUpdateUrl(context, url);

              if (!info.updateRequired && context.mounted) {
                Navigator.of(context).pop();
              }
            },
            child: const Text('Update Now'),
          ),
        ],
      ),
    ),
  );
}
